"""
Monica AI - Interrupt Manager (Barge-In System)

Implements full-duplex voice interaction with barge-in support:
- Voice Activity Detection (VAD) monitors mic while Monica speaks
- When user speaks, Monica immediately stops talking
- Interrupted task is saved and can be resumed on command
- User preferences for "stop doing X" are remembered persistently

Architecture:
  STT (mic) --> VAD --> InterruptManager --> TTS.stop()
                                         --> AI.save_interrupted_task()
                                         --> AI.process_new_input()

Supports:
- Instant barge-in (user talks over Monica)
- "Stop doing X" commands (remembered across sessions)
- "Resume" / "continue" commands
- Persistent suppression list (things Monica should not do)
"""
import json
import logging
import threading
import time
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field

logger = logging.getLogger("Monica.Interrupt")


@dataclass
class InterruptedTask:
    """A task that was interrupted and can be resumed."""
    task_type: str  # "speaking", "teaching", "explaining", etc.
    content: str  # The full text/content
    progress: str  # What was already delivered
    remaining: str  # What's left to deliver
    timestamp: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class InterruptManager:
    """
    Central coordinator for Monica's barge-in / interrupt system.

    Features:
    - Real-time interrupt detection via energy-based VAD
    - Immediate TTS stop on user speech
    - Task memory: saves what Monica was doing when interrupted
    - Resume capability: "continue" / "resume" restores interrupted task
    - Suppression list: "stop doing X" remembered across sessions
    - Preferences memory: persistent user preferences for behavior control
    """

    # Keywords that trigger resume
    RESUME_KEYWORDS = [
        "continue", "resume", "go on", "keep going", "go ahead",
        "carry on", "finish what you were saying", "you were saying",
        "what were you saying", "continue where you left off",
        "keep reading", "keep talking", "never mind keep",
        "never mind, keep", "where you left off", "where were you",
        "nevermind continue", "never mind continue", "nevermind keep",
        "continue reading", "resume reading", "resume where",
        "start again", "say that again", "repeat that",
        "what was that", "can you repeat", "say it again",
    ]

    # Keywords that trigger stop/suppress
    STOP_KEYWORDS = [
        "stop", "shut up", "be quiet", "enough", "hold on",
        "wait", "pause", "quiet", "silence", "hush", "stop talking",
    ]

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator

        # State
        self._is_monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Interrupt state
        self._interrupted_task: Optional[InterruptedTask] = None
        self._interrupt_history: List[InterruptedTask] = []

        # Suppression list: things Monica should NOT do (persisted)
        self._suppression_list: Dict[str, str] = {}  # {behavior: reason}

        # VAD settings
        self.vad_energy_threshold = 0.015  # Mic energy above this = user speaking
        self.vad_min_duration_ms = 150  # Min speech duration to trigger interrupt
        self.interrupt_cooldown = 1.0  # Seconds between interrupts

        # Callbacks
        self._on_interrupt_callbacks: List[Callable] = []
        self._on_resume_callbacks: List[Callable] = []

        # Timing
        self._last_interrupt_time = 0.0

        # Load persistent data
        self._data_dir = self._get_data_dir()
        self._load_suppression_list()
        self._load_preferences()

        logger.info("InterruptManager initialized")

    def _get_data_dir(self) -> Path:
        try:
            from config.settings import config
            d = Path(str(config.BASE_DIR)) / "data" / "user_profile"
        except Exception:
            d = Path("data") / "user_profile"
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ==================== VAD / Monitoring ====================

    def start_monitoring(self):
        """Start VAD monitoring in background thread."""
        if self._is_monitoring:
            return
        self._is_monitoring = True
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._vad_monitor_loop, daemon=True, name="vad-monitor"
        )
        self._monitor_thread.start()
        logger.info("VAD barge-in monitoring started")

    def stop_monitoring(self):
        """Stop VAD monitoring."""
        self._is_monitoring = False
        self._stop_event.set()
        logger.info("VAD monitoring stopped")

    def _vad_monitor_loop(self):
        """
        Background loop: monitors mic while TTS is playing.
        Uses Silero VAD (GPU-accelerated, millisecond detection) if available,
        falls back to energy-based VAD.
        
        Architecture (matches Gemini Live API spec):
        - Thread A (this): constantly runs VAD on mic input
        - When is_speech=True AND Monica is speaking: send kill signal to TTS
        - TTS thread checks interrupt_event before each sentence chunk
        """
        try:
            import pyaudio
            import numpy as np
        except ImportError:
            logger.warning("pyaudio/numpy not available - VAD monitoring disabled")
            return

        # Try to load Silero VAD (GPU-accelerated, recommended by Gemini spec)
        silero_vad = None
        try:
            import torch
            silero_vad, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False,
                trust_repo=True,
            )
            (get_speech_timestamps, _, read_audio, _, _) = utils
            logger.info("Silero VAD loaded (GPU-accelerated barge-in detection)")
        except Exception as e:
            logger.info(f"Silero VAD not available ({e}), using energy-based VAD")
            silero_vad = None

        pa = pyaudio.PyAudio()
        stream = None

        try:
            # Find input device and its native rate (same mic as STT service)
            device_index = None
            capture_rate = 44100  # Default to 44100 (Maonocaster native rate)
            if self.orchestrator:
                stt = self.orchestrator.get_service('stt')
                if stt:
                    device_index = getattr(stt, 'input_device_index', None)
                    # Get the native rate from STT if available
                    stt_rate = getattr(stt, '_capture_rate', None)
                    if stt_rate:
                        capture_rate = stt_rate

            chunk_size = int(capture_rate * 0.032)  # ~32ms chunks
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=capture_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=chunk_size,
            )

            speech_start = None

            while not self._stop_event.is_set():
                try:
                    data = stream.read(chunk_size, exception_on_overflow=False)
                    # Convert int16 to float32 for VAD processing
                    audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                    # Only care about interrupts when Monica is speaking
                    is_tts_active = False
                    if self.orchestrator:
                        is_tts_active = self.orchestrator.get_shared('tts_speaking', False)

                    if not is_tts_active:
                        speech_start = None
                        time.sleep(0.01)
                        continue

                    # Detect speech using Silero VAD or energy fallback
                    is_speech = False
                    if silero_vad is not None:
                        try:
                            import torch
                            # Silero VAD expects 16kHz audio — resample if needed
                            if capture_rate != 16000:
                                ratio = 16000 / capture_rate
                                target_len = int(len(audio) * ratio)
                                indices = np.linspace(0, len(audio) - 1, target_len)
                                audio_16k = np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)
                            else:
                                audio_16k = audio
                            tensor = torch.from_numpy(audio_16k)
                            confidence = silero_vad(tensor, 16000).item()
                            is_speech = confidence > 0.5
                        except Exception:
                            # Silero failed, fall back to energy
                            energy = float(np.sqrt(np.mean(audio ** 2)))
                            is_speech = energy > self.vad_energy_threshold
                    else:
                        energy = float(np.sqrt(np.mean(audio ** 2)))
                        is_speech = energy > self.vad_energy_threshold

                    if is_speech:
                        if speech_start is None:
                            speech_start = time.time()
                        elif (time.time() - speech_start) * 1000 >= self.vad_min_duration_ms:
                            # User has been speaking long enough - trigger interrupt
                            self._trigger_interrupt("vad_barge_in")
                            speech_start = None
                    else:
                        speech_start = None

                except Exception:
                    time.sleep(0.01)

                time.sleep(0.01)  # ~100Hz polling

        except Exception as e:
            logger.warning(f"VAD monitor error: {e}")
        finally:
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            pa.terminate()

    # ==================== Interrupt Logic ====================

    def _trigger_interrupt(self, source: str = "manual"):
        """Trigger an interrupt - stop Monica's current output."""
        now = time.time()
        if now - self._last_interrupt_time < self.interrupt_cooldown:
            return  # Cooldown active
        self._last_interrupt_time = now

        logger.info(f"INTERRUPT triggered (source={source})")

        # 1. Stop TTS immediately
        if self.orchestrator:
            tts = self.orchestrator.get_service('tts')
            if tts:
                # Save what Monica was saying before stopping
                current_text = self.orchestrator.get_shared('tts_text', '')
                spoken_text = self.orchestrator.get_shared('tts_spoken_so_far', '')
                if current_text:
                    remaining = current_text
                    if spoken_text and current_text.startswith(spoken_text):
                        remaining = current_text[len(spoken_text):]
                    elif spoken_text:
                        # Approximate: find where spoken text ends
                        idx = current_text.find(spoken_text[-50:]) if len(spoken_text) > 50 else -1
                        if idx >= 0:
                            remaining = current_text[idx + len(spoken_text[-50:]):]

                    self._interrupted_task = InterruptedTask(
                        task_type="speaking",
                        content=current_text,
                        progress=spoken_text or "",
                        remaining=remaining.strip(),
                    )
                    self._interrupt_history.append(self._interrupted_task)
                    # Keep only last 10
                    if len(self._interrupt_history) > 10:
                        self._interrupt_history = self._interrupt_history[-10:]

                tts.stop_speaking()
                logger.info(f"TTS stopped. Remaining text saved ({len(self._interrupted_task.remaining if self._interrupted_task else '')} chars)")

            self.orchestrator.set_shared('interrupt_active', True)
            self.orchestrator.set_shared('interrupt_time', now)

        # 2. Notify callbacks
        for cb in self._on_interrupt_callbacks:
            try:
                cb(source)
            except Exception as e:
                logger.debug(f"Interrupt callback error: {e}")

    def check_user_command(self, text: str) -> Optional[str]:
        """
        Check if user text is an interrupt/resume/stop command.
        Returns action taken or None if not a command.

        This is called by the AI service on every user message.
        """
        text_lower = text.lower().strip()

        # Check for resume commands
        if any(kw in text_lower for kw in self.RESUME_KEYWORDS):
            return self._handle_resume()

        # Check for "stop doing X" commands (persistent suppression)
        if self._is_stop_behavior_command(text_lower):
            return self._handle_stop_behavior(text_lower)

        # Check for "start doing X again" / "resume X"
        if self._is_resume_behavior_command(text_lower):
            return self._handle_resume_behavior(text_lower)

        # Check for immediate stop commands
        if any(text_lower == kw or text_lower.startswith(kw + " ") for kw in self.STOP_KEYWORDS[:5]):
            self._trigger_interrupt("voice_command")
            return "stopped"

        return None

    # ==================== Resume ====================

    def _handle_resume(self) -> str:
        """Resume the last interrupted task."""
        if not self._interrupted_task:
            return "resume_nothing"

        task = self._interrupted_task
        self._interrupted_task = None

        if self.orchestrator:
            self.orchestrator.set_shared('interrupt_active', False)

        # Resume speaking
        if task.remaining and self.orchestrator:
            tts = self.orchestrator.get_service('tts')
            if tts:
                tts.speak(task.remaining)
                logger.info(f"Resumed speaking: {task.remaining[:60]}...")

        for cb in self._on_resume_callbacks:
            try:
                cb(task)
            except Exception:
                pass

        return "resumed"

    def get_interrupted_task(self) -> Optional[InterruptedTask]:
        """Get the current interrupted task (for AI context)."""
        return self._interrupted_task

    # ==================== Suppression List ("Stop doing X") ====================

    def _is_stop_behavior_command(self, text: str) -> bool:
        """Check if text is a 'stop doing X' command."""
        prefixes = [
            "stop ", "don't ", "dont ", "do not ", "never ", "quit ",
            "please stop ", "please don't ", "please dont ", "please do not ",
            "i don't want you to ", "i dont want you to ",
            "can you stop ", "could you stop ", "would you stop ",
            "stop always ", "you don't need to ", "you dont need to ",
        ]
        # Must have content after the prefix
        for prefix in prefixes:
            if text.startswith(prefix) and len(text) > len(prefix) + 3:
                # Exclude simple stop commands (handled separately)
                remainder = text[len(prefix):].strip()
                if remainder and remainder not in ["talking", "it", "that", "now"]:
                    return True
        return False

    def _handle_stop_behavior(self, text: str) -> str:
        """Parse and save a 'stop doing X' command."""
        # Extract the behavior
        behavior = text
        for prefix in ["please ", "can you ", "could you ", "would you ",
                        "i don't want you to ", "i dont want you to ",
                        "you don't need to ", "you dont need to "]:
            if behavior.startswith(prefix):
                behavior = behavior[len(prefix):]

        for prefix in ["stop ", "don't ", "dont ", "do not ", "never ", "quit "]:
            if behavior.startswith(prefix):
                behavior = behavior[len(prefix):]
                break

        behavior = behavior.strip().rstrip(".")

        if behavior:
            self._suppression_list[behavior] = time.strftime("%Y-%m-%d %H:%M:%S")
            self._save_suppression_list()
            logger.info(f"Suppression added: '{behavior}'")
            return f"suppressed:{behavior}"

        return "stopped"

    def _is_resume_behavior_command(self, text: str) -> bool:
        """Check if text asks to resume a suppressed behavior."""
        prefixes = [
            "you can ", "start ", "resume ", "go back to ",
            "please start ", "it's ok to ", "its ok to ",
            "you may ", "feel free to ",
        ]
        suffixes = [" again", " now", " please"]
        for prefix in prefixes:
            if text.startswith(prefix):
                return True
        for suffix in suffixes:
            if text.endswith(suffix) and any(text.startswith(p) for p in prefixes):
                return True
        return False

    def _handle_resume_behavior(self, text: str) -> str:
        """Remove a behavior from suppression list."""
        # Extract behavior name
        behavior = text
        for prefix in ["please ", "you can ", "start ", "resume ", "go back to ",
                        "it's ok to ", "its ok to ", "you may ", "feel free to "]:
            if behavior.startswith(prefix):
                behavior = behavior[len(prefix):]
        for suffix in [" again", " now", " please"]:
            if behavior.endswith(suffix):
                behavior = behavior[:-len(suffix)]
        behavior = behavior.strip()

        # Find and remove from suppression list (fuzzy match: stem overlap)
        removed = False
        keys_to_remove = []
        behavior_words = set(behavior.lower().split())
        for key in self._suppression_list:
            key_words = set(key.lower().split())
            # Match if: substring match OR 50%+ word overlap OR common stem
            overlap = len(behavior_words & key_words)
            if (behavior in key or key in behavior
                    or overlap >= max(1, len(min(behavior_words, key_words, key=len)) // 2)
                    or any(kw[:4] in behavior for kw in key_words if len(kw) >= 4)
                    or any(bw[:4] in key for bw in behavior_words if len(bw) >= 4)):
                keys_to_remove.append(key)
                removed = True

        for key in keys_to_remove:
            del self._suppression_list[key]

        if removed:
            self._save_suppression_list()
            logger.info(f"Suppression removed: '{behavior}'")
            return f"unsuppressed:{behavior}"

        return None

    def get_suppression_list(self) -> Dict[str, str]:
        """Get current suppression list (for AI context)."""
        return dict(self._suppression_list)

    def is_suppressed(self, behavior: str) -> bool:
        """Check if a behavior is currently suppressed."""
        behavior_lower = behavior.lower()
        for key in self._suppression_list:
            if key.lower() in behavior_lower or behavior_lower in key.lower():
                return True
        return False

    def get_context_for_prompt(self) -> str:
        """Get interrupt/suppression context for AI system prompt."""
        parts = []

        if self._suppression_list:
            items = ", ".join(self._suppression_list.keys())
            parts.append(
                f"\nIMPORTANT - The user has asked you to STOP doing these things: [{items}]. "
                f"Do NOT do any of these unless the user explicitly asks you to resume."
            )

        if self._interrupted_task:
            parts.append(
                f"\nYou were interrupted while saying: '{self._interrupted_task.remaining[:100]}...' "
                f"If the user says 'continue' or 'resume', finish what you were saying."
            )

        return "".join(parts)

    # ==================== Persistence ====================

    def _load_suppression_list(self):
        path = self._data_dir / "suppression_list.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._suppression_list = json.load(f)
                logger.info(f"Loaded {len(self._suppression_list)} suppressed behaviors")
            except Exception:
                pass

    def _save_suppression_list(self):
        path = self._data_dir / "suppression_list.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._suppression_list, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save suppression list: {e}")

    def _load_preferences(self):
        """Load user interaction preferences."""
        path = self._data_dir / "interaction_prefs.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    prefs = json.load(f)
                self.vad_energy_threshold = prefs.get("vad_threshold", self.vad_energy_threshold)
                self.interrupt_cooldown = prefs.get("interrupt_cooldown", self.interrupt_cooldown)
            except Exception:
                pass

    # ==================== Callbacks ====================

    def on_interrupt(self, callback: Callable):
        """Register callback for when an interrupt occurs."""
        self._on_interrupt_callbacks.append(callback)

    def on_resume(self, callback: Callable):
        """Register callback for when a task is resumed."""
        self._on_resume_callbacks.append(callback)


# Singleton
_interrupt_mgr = None


def get_interrupt_manager(orchestrator=None) -> InterruptManager:
    global _interrupt_mgr
    if _interrupt_mgr is None:
        _interrupt_mgr = InterruptManager(orchestrator)
    return _interrupt_mgr
