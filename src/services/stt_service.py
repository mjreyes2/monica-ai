"""
Speech-to-Text Service for Monica AI.
Wraps SpeechBrain / Whisper / other STT backends into a managed service.
Uses custom-trained FinalSpeechBrainRecognizer with personal voice model
(2500+ recorded phrases, voice adaptation, personal vocabulary).
"""

import threading
import time
import logging
import queue
import os
import sys
import json
import re
import numpy as np
from pathlib import Path
from typing import Optional, Callable, List, Any

logger = logging.getLogger("Monica.STT")


class STTService:
    """
    Speech-to-Text service with microphone capture and transcription.
    
    Features:
    - Custom-trained FinalSpeechBrainRecognizer (primary, uses personal voice model)
    - SpeechBrain wav2vec2 (fallback)
    - Whisper (fallback)
    - Local offline recognition (last resort, NO cloud APIs)
    - Wake word detection
    - Energy-based voice activity detection
    - Personal vocabulary and voice adaptation
    - Configurable microphone device selection
    - Thread-safe transcription queue
    """

    def __init__(self, orchestrator, config: dict = None):
        self.orchestrator = orchestrator
        self.config = config or {}
        
        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        self.input_device_name = self.config.get('INPUT_DEVICE_NAME', None)
        self.input_device_index = self.config.get('INPUT_DEVICE_INDEX', None)
        
        # State
        self.is_listening = False
        self.is_initialized = False
        self.stop_event = threading.Event()
        self._stream_reconfigure = threading.Event()
        
        # Transcription results
        self.transcript_queue = queue.Queue()
        self.last_transcript = ""
        self.callbacks: List[Callable[[str], None]] = []
        
        # Audio stream
        self.audio_stream = None
        self.recognizer = None
        
        # Personal voice model paths (from config or auto-detected)
        self.personal_voice_model_dir = self.config.get('PERSONAL_VOICE_MODEL_DIR', None)
        self.voice_adaptation_model = self.config.get('VOICE_ADAPTATION_MODEL', None)
        self.personal_vocabulary_path = self.config.get('PERSONAL_VOCABULARY', None)
        self.personal_vocabulary = {}
        
        # Energy-based VAD
        self.energy_threshold = float(self.config.get('ENERGY_THRESHOLD', 0.01))
        self.pause_threshold = float(self.config.get('PAUSE_THRESHOLD', 1.5))
        self._energy_calibrated = False
        self._min_speech_duration = float(self.config.get('MIN_SPEECH_DURATION', 0.55))
        self._max_speech_duration = float(self.config.get('MAX_SPEECH_DURATION', 14.0))
        self._quality_min_chars = int(self.config.get('STT_QUALITY_MIN_CHARS', 2))
        self._quality_min_tokens = int(self.config.get('STT_QUALITY_MIN_TOKENS', 1))
        self._wake_score_threshold = float(self.config.get('WAKE_SCORE_THRESHOLD', 1.0))
        self._weak_tokens = {
            'a', 'i', 'an', 'uh', 'um', 'hmm', 'mm', 'ah', 'oh', 'eh', 'mhm'
        }
        self._short_command_allowlist = {
            'stop', 'quiet', 'silence', 'yes', 'no', 'help', 'zoom', 'resume'
        }
        
        logger.info("STT Service created")

    def initialize(self):
        """Initialize the STT engine - prefer custom trained model, with Whisper fallback."""
        # Load personal vocabulary if available
        self._load_personal_vocabulary()
        
        try:
            # Try custom-trained FinalSpeechBrainRecognizer first (trained on YOUR voice)
            self._init_custom_trained()
        except Exception as e:
            logger.warning(f"Custom trained model init failed: {e}")
            try:
                # Fall back to standard SpeechBrain
                self._init_speechbrain()
            except Exception as e2:
                logger.warning(f"SpeechBrain init failed: {e2}")
                try:
                    self._init_whisper()
                except Exception as e3:
                    logger.warning(f"Whisper init failed: {e3}")
                    self._init_fallback()
        
        # Also load Whisper as secondary engine for reliability
        self._whisper_model = None
        if self.engine_type != "whisper":
            try:
                import whisper
                # Try 'base' first (74MB, fast download) for guaranteed availability
                self._whisper_model = whisper.load_model("base")
                logger.info("Whisper loaded as secondary STT engine (base model, fallback)")
            except Exception:
                pass
        
        self.is_initialized = True
        if self.engine_type == "none" and self._whisper_model is None:
            logger.warning("STT Service: NO engine available! Whisper will be loaded on first speech segment.")
        logger.info(f"STT Service initialized (engine={self.engine_type}, whisper_fallback={'yes' if self._whisper_model else 'on-demand'})")

    def _load_personal_vocabulary(self):
        """Load personal vocabulary for better recognition accuracy."""
        try:
            if self.personal_vocabulary_path and os.path.exists(self.personal_vocabulary_path):
                with open(self.personal_vocabulary_path, 'r', encoding='utf-8') as f:
                    self.personal_vocabulary = json.load(f)
                logger.info(f"Personal vocabulary loaded ({len(self.personal_vocabulary)} entries)")
            else:
                # Auto-detect from project structure
                project_root = Path(__file__).resolve().parents[2]
                vocab_path = project_root / "monica_ai" / "personal_voice_model" / "personal_vocabulary.json"
                if vocab_path.exists():
                    with open(vocab_path, 'r', encoding='utf-8') as f:
                        self.personal_vocabulary = json.load(f)
                    self.personal_vocabulary_path = str(vocab_path)
                    logger.info(f"Personal vocabulary auto-loaded ({len(self.personal_vocabulary)} entries)")
        except Exception as e:
            logger.debug(f"Could not load personal vocabulary: {e}")

    def _init_custom_trained(self):
        """Initialize custom-trained FinalSpeechBrainRecognizer with personal voice model.
        
        The trained model lives in monica_ai/src/audio/speechbrain_final.py.
        We use importlib to load it by absolute path so there's no conflict
        with the main project's src/audio/ package.
        """
        import importlib.util
        project_root = Path(__file__).resolve().parents[2]
        monica_ai_audio = project_root / "monica_ai" / "src" / "audio"
        module_path = monica_ai_audio / "speechbrain_final.py"
        
        if not module_path.exists():
            raise RuntimeError(f"speechbrain_final.py not found at {module_path}")
        
        # Ensure monica_ai/src is on path for sub-imports (torch_patch, etc.)
        monica_ai_src = str(project_root / "monica_ai" / "src")
        if monica_ai_src not in sys.path:
            sys.path.insert(0, monica_ai_src)
        
        try:
            # Load torch_patch first (speechbrain_final does 'from . import torch_patch')
            tp_path = monica_ai_audio / "torch_patch.py"
            if tp_path.exists():
                tp_spec = importlib.util.spec_from_file_location(
                    "monica_ai_audio.torch_patch", str(tp_path))
                tp_mod = importlib.util.module_from_spec(tp_spec)
                sys.modules["monica_ai_audio.torch_patch"] = tp_mod
                try:
                    tp_spec.loader.exec_module(tp_mod)
                except Exception:
                    pass  # torch_patch may fail gracefully
            
            # Register a virtual package so relative imports resolve
            import types
            if "monica_ai_audio" not in sys.modules:
                pkg = types.ModuleType("monica_ai_audio")
                pkg.__path__ = [str(monica_ai_audio)]
                sys.modules["monica_ai_audio"] = pkg
            
            spec = importlib.util.spec_from_file_location(
                "monica_ai_audio.speechbrain_final",
                str(module_path),
                submodule_search_locations=[str(monica_ai_audio)]
            )
            mod = importlib.util.module_from_spec(spec)
            # Redirect relative imports: 'from . import X' → look in monica_ai_audio
            mod.__package__ = "monica_ai_audio"
            sys.modules[spec.name] = mod
            spec.loader.exec_module(mod)
            
            FinalSpeechBrainRecognizer = mod.FinalSpeechBrainRecognizer
            self.recognizer = FinalSpeechBrainRecognizer()
            self.engine_type = "custom_trained"
            logger.info("Custom-trained FinalSpeechBrainRecognizer loaded (personal voice model)")
            
            # Log training data info
            if self.voice_adaptation_model and os.path.exists(self.voice_adaptation_model):
                size_mb = os.path.getsize(self.voice_adaptation_model) / (1024 * 1024)
                logger.info(f"Voice adaptation model: {size_mb:.1f} MB")
        except ImportError as e:
            raise RuntimeError(f"FinalSpeechBrainRecognizer not available: {e}")
        except Exception as e:
            raise RuntimeError(f"Custom trained model failed to initialize: {e}")

    def _init_speechbrain(self):
        """Initialize standard SpeechBrain ASR as fallback."""
        try:
            from speechbrain.inference.ASR import EncoderDecoderASR
            self.recognizer = EncoderDecoderASR.from_hparams(
                source="speechbrain/asr-wav2vec2-commonvoice-en",
                savedir="pretrained_models/asr-wav2vec2-commonvoice-en"
            )
            self.engine_type = "speechbrain"
            logger.info("SpeechBrain ASR loaded (standard model)")
        except ImportError:
            raise RuntimeError("SpeechBrain not available")

    def _init_whisper(self):
        """Initialize Whisper ASR as fallback.
        
        Uses 'base' model: 74M params, ~1GB VRAM, good accuracy.
        With RTX 4060 CUDA, transcription is near real-time.
        """
        try:
            import whisper
            # Try 'small' first for best accuracy, fall back to 'base' (smaller download)
            for model_name in ("small", "base"):
                try:
                    self.recognizer = whisper.load_model(model_name)
                    self.engine_type = "whisper"
                    device = next(self.recognizer.parameters()).device
                    logger.info(f"Whisper ASR loaded ({model_name} model, device={device})")
                    return
                except Exception as me:
                    logger.warning(f"Whisper '{model_name}' model failed: {me}")
            raise RuntimeError("All Whisper models failed to load")
        except ImportError:
            raise RuntimeError("Whisper not available - pip install openai-whisper")
        except Exception as e:
            raise RuntimeError(f"Whisper init failed: {e}")

    def _init_fallback(self):
        """Initialize LOCAL offline STT as last resort.
        
        PRIVACY: We do NOT use recognize_google() as it sends audio
        to Google servers. All STT must be 100% local.
        """
        # Try Vosk (fully offline, lightweight)
        try:
            from vosk import Model as VoskModel, KaldiRecognizer
            # Look for vosk model in models/ directory
            project_root = Path(__file__).resolve().parents[2]
            vosk_model_path = project_root / "models" / "vosk-model-small-en-us-0.15"
            if not vosk_model_path.exists():
                vosk_model_path = project_root / "models" / "vosk"
            if vosk_model_path.exists():
                self.recognizer = VoskModel(str(vosk_model_path))
                self.engine_type = "vosk"
                logger.info("Using Vosk offline STT (100% local, no cloud)")
                return
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Vosk init failed: {e}")
        
        # Last resort: speech_recognition with Sphinx (offline only)
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.engine_type = "sphinx_offline"
            logger.info("Using PocketSphinx offline STT (100% local, no cloud)")
        except ImportError:
            self.engine_type = "none"
            logger.error("No STT engine available")

    def run(self):
        """Main STT loop - capture audio and transcribe."""
        if not self.is_initialized:
            self.initialize()
        
        self.is_listening = True
        logger.info("STT listening started")
        
        try:
            if self.engine_type in ("sphinx_offline", "speech_recognition"):
                self._run_speech_recognition_loop()
            else:
                self._run_streaming_loop()
        except Exception as e:
            logger.error(f"STT loop error: {e}")
        finally:
            self.is_listening = False

    def _run_speech_recognition_loop(self):
        """Run using the speech_recognition library."""
        import speech_recognition as sr
        
        mic = sr.Microphone(
            device_index=self.input_device_index,
            sample_rate=self.sample_rate
        )
        
        with mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Ambient noise adjusted")
            
            while not self.stop_event.is_set():
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=30)
                    
                    # Transcribe in background thread
                    threading.Thread(
                        target=self._transcribe_sr,
                        args=(audio,),
                        daemon=True
                    ).start()
                    
                except Exception:
                    continue

    def _transcribe_sr(self, audio):
        """Transcribe using LOCAL offline engines only.
        
        PRIVACY: NEVER uses recognize_google() which sends audio to cloud.
        Uses PocketSphinx (offline) or returns empty.
        """
        try:
            import speech_recognition as sr
            # Use PocketSphinx (100% offline) - NEVER Google
            try:
                text = self.recognizer.recognize_sphinx(audio)
            except (sr.UnknownValueError, sr.RequestError):
                text = None
            except AttributeError:
                # Sphinx not installed, try offline Vosk via sr
                try:
                    text = self.recognizer.recognize_vosk(audio)
                    if text:
                        import json
                        result = json.loads(text)
                        text = result.get('text', '')
                except Exception:
                    text = None
            if text and text.strip():
                self._on_transcript(text.strip())
        except Exception:
            pass

    def _resample(self, audio: np.ndarray, orig_rate: int, target_rate: int) -> np.ndarray:
        """Resample audio using scipy (high quality) or polyphase fallback."""
        if orig_rate == target_rate:
            return audio
        try:
            from scipy.signal import resample_poly
            from math import gcd
            g = gcd(orig_rate, target_rate)
            up = target_rate // g
            down = orig_rate // g
            return resample_poly(audio, up, down).astype(np.float32)
        except ImportError:
            # Fallback: linear interpolation (lower quality)
            target_len = int(len(audio) * target_rate / orig_rate)
            indices = np.linspace(0, len(audio) - 1, target_len)
            return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)

    def _find_mic(self, pa):
        """Find a working microphone. Returns (device_index, native_sample_rate)."""
        import pyaudio

        # If explicitly configured index, use it
        if self.input_device_index is not None:
            try:
                info = pa.get_device_info_by_index(int(self.input_device_index))
                if info.get('maxInputChannels', 0) > 0:
                    rate = int(info.get('defaultSampleRate', 44100))
                    logger.info(f"Using configured mic [{self.input_device_index}] {info.get('name')} @ {rate}Hz")
                    return int(self.input_device_index), rate
            except Exception:
                pass

        # Search by name (configured or default 'Maonocaster')
        search_names = []
        if self.input_device_name:
            search_names.append(self.input_device_name.lower())
        search_names.extend(['maonocaster', 'headset microphone', 'microphone'])

        for target in search_names:
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) <= 0:
                    continue
                name = info.get('name', '').lower()
                # Skip virtual/placeholder devices
                if any(x in name for x in ('sound mapper', 'voicemod', 'virtual', 'monitor', 'loopback', 'stereo mix')):
                    continue
                if target in name:
                    rate = int(info.get('defaultSampleRate', 44100))
                    logger.info(f"Found mic [{i}] {info.get('name')} @ {rate}Hz (matched '{target}')")
                    return i, rate

        # Last resort: first non-virtual input device
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info.get('maxInputChannels', 0) <= 0:
                continue
            name = info.get('name', '').lower()
            if any(x in name for x in ('sound mapper', 'voicemod', 'virtual', 'monitor', 'loopback', 'stereo mix')):
                continue
            rate = int(info.get('defaultSampleRate', 44100))
            logger.info(f"Fallback mic [{i}] {info.get('name')} @ {rate}Hz")
            return i, rate

        logger.warning("No microphone found, using system default")
        return None, 44100

    def _run_streaming_loop(self):
        """Run streaming ASR with PyAudio."""
        try:
            import pyaudio
            
            pa = pyaudio.PyAudio()
            while not self.stop_event.is_set():
                self._stream_reconfigure.clear()

                device_index, capture_rate = self._find_mic(pa)
                self._capture_rate = capture_rate  # Expose for interrupt manager VAD

                stream = pa.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=capture_rate,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=self.chunk_size,
                )

                # Calibrate energy threshold
                if not self._energy_calibrated:
                    logger.info("Calibrating ambient noise (1 second)...")
                    noise_energies = []
                    for _ in range(int(capture_rate / self.chunk_size)):
                        try:
                            data = stream.read(self.chunk_size, exception_on_overflow=False)
                            chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                            noise_energies.append(np.sqrt(np.mean(chunk ** 2)))
                        except Exception:
                            pass
                    if noise_energies:
                        ambient = np.mean(noise_energies)
                        # Min 0.02 prevents false triggers; max 0.05 prevents hot-mic lockout
                        self.energy_threshold = min(max(ambient * 2.0, 0.02), 0.05)
                        logger.info(f"Ambient: {ambient:.6f}, threshold: {self.energy_threshold:.6f}")
                    self._energy_calibrated = True

                audio_buffer = []
                silence_start = None
                speech_start = None

                tts_was_active = False
                tts_ended_at = 0.0
                TTS_COOLDOWN = 1.0  # seconds to ignore mic after TTS stops

                barge_in_start = None
                barge_in_chunks = []  # Collect user audio during barge-in
                BARGE_IN_ENERGY = 0.05  # Energy threshold — above ambient (~0.009) and TTS echo (~0.02 on headset)
                BARGE_IN_DURATION = 0.25  # seconds of sustained speech to trigger interrupt
                _barge_log_counter = 0
                barge_in_just_triggered = False  # Skip cooldown after barge-in

                while not self.stop_event.is_set() and not self._stream_reconfigure.is_set():
                    try:
                        # While TTS is speaking: monitor for barge-in instead of discarding
                        is_tts_active = self.orchestrator and self.orchestrator.get_shared('tts_speaking')
                        if is_tts_active:
                            tts_was_active = True
                            audio_buffer = []
                            silence_start = None
                            speech_start = None
                            # Read audio and check for barge-in (user speaking over Monica)
                            try:
                                data = stream.read(self.chunk_size, exception_on_overflow=False)
                                chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                                energy = float(np.sqrt(np.mean(chunk ** 2)))
                                _barge_log_counter += 1
                                if _barge_log_counter % 80 == 0:
                                    logger.debug(f"TTS active - mic energy: {energy:.4f} (threshold: {BARGE_IN_ENERGY})")
                                if energy > BARGE_IN_ENERGY:
                                    barge_in_chunks.append(chunk)
                                    if barge_in_start is None:
                                        barge_in_start = time.time()
                                    elif time.time() - barge_in_start >= BARGE_IN_DURATION:
                                        # User has been speaking long enough — stop Monica
                                        logger.info(f"BARGE-IN detected (energy={energy:.3f}, duration={time.time()-barge_in_start:.1f}s)")
                                        im = self.orchestrator.get_service('ai')
                                        im = getattr(im, 'interrupt_manager', None) if im else None
                                        if im and hasattr(im, '_trigger_interrupt'):
                                            im._trigger_interrupt("stt_barge_in")
                                        else:
                                            tts = self.orchestrator.get_service('tts')
                                            if tts:
                                                tts.stop_speaking()
                                        barge_in_start = None
                                        barge_in_just_triggered = True
                                        # Feed barge-in audio into normal buffer so it gets transcribed
                                        audio_buffer = list(barge_in_chunks)
                                        speech_start = time.time() - BARGE_IN_DURATION
                                        barge_in_chunks = []
                                else:
                                    barge_in_start = None
                                    barge_in_chunks = []
                            except Exception:
                                pass
                            time.sleep(0.01)
                            continue

                        # Post-TTS cooldown: flush residual echo from mic buffer
                        # BUT skip cooldown if barge-in just triggered (user is talking)
                        if tts_was_active:
                            tts_was_active = False
                            if barge_in_just_triggered:
                                barge_in_just_triggered = False
                                tts_ended_at = 0.0  # No cooldown
                                # Keep audio_buffer — it has the user's barge-in audio
                                silence_start = None
                                logger.info("Skipping post-TTS cooldown (barge-in active, listening for command)")
                            else:
                                tts_ended_at = time.time()
                                audio_buffer = []
                                silence_start = None
                                speech_start = None
                                try:
                                    for _ in range(20):
                                        stream.read(self.chunk_size, exception_on_overflow=False)
                                except Exception:
                                    pass
                                continue

                        if time.time() - tts_ended_at < TTS_COOLDOWN:
                            try:
                                stream.read(self.chunk_size, exception_on_overflow=False)
                            except Exception:
                                pass
                            continue

                        data = stream.read(self.chunk_size, exception_on_overflow=False)
                        audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                        energy = np.sqrt(np.mean(audio_chunk ** 2))

                        # Publish mic energy for GUI level bar
                        if self.orchestrator:
                            self.orchestrator.set_shared('mic_energy', float(energy))

                        if energy > self.energy_threshold:
                            if not audio_buffer:
                                speech_start = time.time()
                            audio_buffer.append(audio_chunk)
                            silence_start = None
                        elif audio_buffer:
                            if silence_start is None:
                                silence_start = time.time()
                            elif time.time() - silence_start > self.pause_threshold:
                                full_audio = np.concatenate(audio_buffer)
                                # Resample to 16kHz for Whisper
                                if capture_rate != 16000:
                                    full_audio = self._resample(full_audio, capture_rate, 16000)
                                duration = len(full_audio) / 16000
                                audio_buffer = []
                                silence_start = None
                                speech_start = None

                                if duration >= self._min_speech_duration:
                                    logger.info(f"Speech segment: {duration:.1f}s, sending to transcription")
                                    segment_rms = float(np.sqrt(np.mean(full_audio ** 2)))
                                    threading.Thread(
                                        target=self._transcribe_audio,
                                        args=(full_audio, duration, segment_rms),
                                        daemon=True
                                    ).start()
                                else:
                                    logger.debug(f"Ignoring short sound: {duration:.2f}s")

                    except Exception:
                        time.sleep(0.01)

                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass

                if self._stream_reconfigure.is_set() and not self.stop_event.is_set():
                    logger.info("Reconfiguring microphone stream...")

            pa.terminate()
            
        except ImportError:
            logger.error("PyAudio not available for streaming STT")
            if self.engine_type != "speech_recognition":
                self._init_fallback()
                self._run_speech_recognition_loop()
        except Exception as e:
            logger.error(f"Streaming STT initialization failed: {e}")

    def _normalize_transcript(self, text: str) -> str:
        """Normalize transcript for quality checks and wake scoring."""
        t = (text or '').strip().lower()
        t = t.replace('_', ' ')
        t = re.sub(r"[^a-z0-9\s']+", ' ', t)
        t = re.sub(r"\s+", ' ', t).strip()
        return t

    def _wake_phrase_score(self, text: str) -> float:
        """Score whether text likely intends the wake phrase."""
        t = self._normalize_transcript(text)
        if not t:
            return 0.0

        monica_forms = ('monica', 'monika', 'monic', 'omega', 'monikah', 'monicah')
        init_forms = (
            'initialize', 'initialise', 'initializing', 'initialising', 'init',
            'interlaced', 'initialoates', 'angel ace', 'in itialize'
        )

        score = 0.0
        if any(m in t for m in monica_forms):
            score += 0.6
        if any(i in t for i in init_forms):
            score += 0.7
        if 'system online' in t or 'startup' in t or 'start up' in t:
            score += 0.4
        return score

    def _is_low_quality_transcript(self, text: str, segment_duration: Optional[float]) -> bool:
        """Reject fragments/noise-like transcripts before wake gating."""
        t = self._normalize_transcript(text)
        if not t:
            return True
        if t in self._short_command_allowlist:
            return False

        tokens = t.split()
        if len(t) < self._quality_min_chars:
            return True
        if len(tokens) < self._quality_min_tokens:
            return True

        # Typical STT fragment outputs observed in logs: "a", "i", "an"
        if len(tokens) == 1 and tokens[0] in self._weak_tokens:
            return True

        # If segment had substantial audio but produced tiny text, it's likely bad decode.
        if segment_duration and segment_duration >= 0.9:
            alpha_chars = sum(ch.isalpha() for ch in t)
            if alpha_chars <= 2 and len(tokens) <= 1:
                return True

        return False

    def _transcribe_audio(self, audio: np.ndarray, segment_duration: Optional[float] = None,
                          segment_rms: Optional[float] = None):
        """Transcribe raw audio data. Each engine is tried independently."""
        text = None

        # --- Speaker verification gate ---
        # If the recognizer supports speaker verification and a voice signature
        # is enrolled, reject audio that doesn't match the owner's voice.
        try:
            if hasattr(self.recognizer, 'verify_speaker') and hasattr(self.recognizer, 'contains_speech'):
                import torch as _torch
                _audio_t = _torch.from_numpy(audio).float()

                # 1. Check if there is actual speech (Silero VAD)
                has_speech, speech_prob, _ = self.recognizer.contains_speech(_audio_t)
                if not has_speech:
                    logger.debug("No speech detected (VAD filtered) — skipping transcription")
                    return

                if speech_prob < 0.45:
                    logger.debug(f"Low speech probability ({speech_prob:.2f}) — skipping transcription")
                    return

                # 2. Verify speaker identity (only if voice signature exists)
                if self.recognizer.voice_signature is not None:
                    is_user, similarity = self.recognizer.verify_speaker(_audio_t, threshold=0.25)
                    if not is_user:
                        logger.info(f"Unknown speaker rejected (similarity: {similarity:.3f})")
                        return
        except Exception as _sv_err:
            logger.debug(f"Speaker verification check skipped: {_sv_err}")
        
        # --- Try primary engine first ---
        try:
            if self.engine_type == "custom_trained":
                import torch
                if hasattr(self.recognizer, 'recognize_tensor'):
                    audio_tensor = torch.from_numpy(audio).float()
                    if audio_tensor.dim() == 1:
                        audio_tensor = audio_tensor.unsqueeze(0)
                    text = self.recognizer.recognize_tensor(audio_tensor)
                    if isinstance(text, (list, tuple)):
                        text = text[0] if text else ''
                    if text and text.strip():
                        logger.info(f"Custom STT: '{text.strip()}'")
                elif hasattr(self.recognizer, 'recognize_file'):
                    text = self._transcribe_via_file(self.recognizer.recognize_file, audio)
            elif self.engine_type == "speechbrain":
                result = self.recognizer.transcribe_batch(
                    audio.unsqueeze(0) if hasattr(audio, 'unsqueeze') else audio
                )
                text = result[0] if isinstance(result, list) else result
            elif self.engine_type == "whisper":
                text = self._transcribe_via_whisper(self.recognizer, audio)
                if text and text.strip():
                    logger.info(f"Whisper primary: '{text.strip()}'") 
            elif self.engine_type == "vosk":
                from vosk import KaldiRecognizer
                import json as _json
                rec = KaldiRecognizer(self.recognizer, self.sample_rate)
                audio_bytes = (audio * 32767).astype(np.int16).tobytes()
                rec.AcceptWaveform(audio_bytes)
                result = _json.loads(rec.FinalResult())
                text = result.get('text', '')
        except Exception as e:
            logger.warning(f"Primary STT ({self.engine_type}) error: {e}")
            text = None
        
        primary_text = (text or '').strip() if isinstance(text, str) else ''
        primary_low_quality = self._is_low_quality_transcript(primary_text, segment_duration)

        # --- Whisper fallback as BACKUP ONLY ---
        # Use Whisper only if primary is empty/failed or clearly low-quality.
        if ((not primary_text) or primary_low_quality) and self._whisper_model is not None:
            try:
                whisper_text = self._transcribe_via_whisper(self._whisper_model, audio)
                whisper_text = whisper_text.strip() if isinstance(whisper_text, str) else ''
                if whisper_text:
                    whisper_low_quality = self._is_low_quality_transcript(whisper_text, segment_duration)
                    # Prefer Whisper only when it materially improves transcript quality.
                    if (not whisper_low_quality) or self._wake_phrase_score(whisper_text) > self._wake_phrase_score(primary_text):
                        text = whisper_text
                        logger.info(f"Whisper backup accepted: '{text}'")
                    else:
                        text = primary_text
                else:
                    text = primary_text
            except Exception as we:
                logger.warning(f"Whisper fallback error: {we}")
                text = primary_text
        
        # --- Last resort: lazy-load Whisper 'base' model on demand ---
        if (not text or not str(text).strip()) and self._whisper_model is None:
            try:
                import whisper
                logger.info("Loading Whisper 'base' model on-demand (first transcription)...")
                self._whisper_model = whisper.load_model("base")
                text = self._transcribe_via_whisper(self._whisper_model, audio)
                if text and text.strip():
                    logger.info(f"Whisper on-demand: '{text.strip()}'")
            except Exception as wd:
                logger.warning(f"Whisper on-demand load error: {wd}")
        
        final_text = text.strip() if isinstance(text, str) else ''
        if final_text:
            if self._is_low_quality_transcript(final_text, segment_duration):
                logger.info(f"Dropping low-quality transcript before gate: '{final_text}'")
                return

            # Share quality metadata for GUI/debug decisions.
            if self.orchestrator:
                self.orchestrator.set_shared('stt_segment_duration', float(segment_duration or 0.0))
                self.orchestrator.set_shared('stt_segment_rms', float(segment_rms or 0.0))
                self.orchestrator.set_shared('stt_wake_score', float(self._wake_phrase_score(final_text)))

            self._on_transcript(final_text)
        else:
            logger.debug("No transcription produced for audio segment")

    def _transcribe_via_whisper(self, model, audio: np.ndarray) -> str:
        """Transcribe audio using Whisper's transcribe() for proper long-form handling.
        Uses sliding-window segmentation instead of single 30s decode().
        NOTE: GC is disabled globally by the GUI to prevent Tcl_AsyncDelete crashes."""
        import whisper
        import torch
        duration = len(audio) / 16000
        logger.info(f"Whisper: transcribing {duration:.1f}s of audio...")
        with torch.inference_mode():
            result = whisper.transcribe(
                model,
                audio,
                language="en",
                fp16=False,
                no_speech_threshold=0.6,
                condition_on_previous_text=True,
                initial_prompt=(
                    "Monica, initialize, show me, zoom in, zoom out, turn the globe, "
                    "enlarge, shrink, show me where, on the globe, "
                    "South Africa, Cairo, Egypt, Shanghai, China, Paris, France, "
                    "London, England, Tokyo, Japan, Los Angeles, California, Florida, "
                    "New York, Brazil, Australia, India, Russia, Germany, Italy, "
                    "Mexico, Canada, Spain, Argentina, Colombia, Nigeria, Kenya, "
                    "Saudi Arabia, Israel, Turkey, Greece, Norway, Sweden, "
                    "physics, biology, thermodynamics, kinetic energy, "
                    "tell me about, what is, explain, stop, continue"
                ),
            )
        if str(model.device).startswith('cuda'):
            torch.cuda.synchronize()
        text = result.get('text', '') if isinstance(result, dict) else str(result)
        logger.info(f"Whisper result: '{text.strip()}'")
        return text.strip()

    def _transcribe_via_file(self, recognize_fn, audio: np.ndarray) -> str:
        """Transcribe audio by saving to temp file and calling recognize function."""
        import tempfile, soundfile as sf
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                tmp_path = f.name
            sf.write(tmp_path, audio, self.sample_rate)
            result = recognize_fn(tmp_path)
            if isinstance(result, (list, tuple)):
                return result[0] if result else ''
            return str(result) if result else ''
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def _on_transcript(self, text: str):
        """Handle new transcription result."""
        self.last_transcript = text
        self.transcript_queue.put(text)
        
        # Share via orchestrator (consumed flag for GUI pickup)
        if self.orchestrator:
            self.orchestrator.set_shared('last_transcript', text)
            self.orchestrator.set_shared('stt_consumed', False)
            self.orchestrator.set_shared('stt_timestamp', time.time())
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(text)
            except Exception as e:
                logger.debug(f"STT callback error: {e}")
        
        logger.info(f"Transcript: {text}")

    def get_transcript(self, timeout: float = None) -> Optional[str]:
        """Get next transcript from queue."""
        try:
            return self.transcript_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def add_callback(self, callback: Callable[[str], None]):
        """Add transcription callback."""
        self.callbacks.append(callback)

    def set_microphone(self, device_index: Optional[int] = None, device_name: Optional[str] = None):
        """Change the microphone device at runtime."""
        self.input_device_index = device_index
        self.input_device_name = device_name
        self._energy_calibrated = False
        self._stream_reconfigure.set()
        logger.info(f"Microphone changed: index={device_index}, name={device_name}")

    @staticmethod
    def list_microphones() -> List[dict]:
        """List all available input audio devices (microphones).
        
        Returns:
            List of dicts with 'index', 'name', 'sample_rate', 'channels' keys.
        """
        devices = []
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    devices.append({
                        'index': i,
                        'name': info.get('name', f'Device {i}'),
                        'sample_rate': int(info.get('defaultSampleRate', 16000)),
                        'channels': int(info.get('maxInputChannels', 1))
                    })
            pa.terminate()
        except ImportError:
            try:
                import sounddevice as sd
                device_list = sd.query_devices()
                for i, d in enumerate(device_list):
                    if d.get('max_input_channels', 0) > 0:
                        devices.append({
                            'index': i,
                            'name': d.get('name', f'Device {i}'),
                            'sample_rate': int(d.get('default_samplerate', 16000)),
                            'channels': int(d.get('max_input_channels', 1))
                        })
            except ImportError:
                logger.warning("Neither pyaudio nor sounddevice available for listing microphones")
        except Exception as e:
            logger.error(f"Error listing microphones: {e}")
        return devices

    def stop(self):
        """Stop the STT service."""
        self.stop_event.set()
        self.is_listening = False
        logger.info("STT Service stopped")
