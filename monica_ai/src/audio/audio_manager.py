"""
Clean Audio Manager module for Monica AI.
Only uses SpeechBrain Personal Voice Recognition - no old models
"""

import numpy as np
import collections
import threading
import queue
import time
from typing import Optional, Callable, List, Dict, Any

# Try to import audio libraries
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("PyAudio not available. Audio input/output will be limited.")

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

# Speech recognition - SpeechBrain personal voice system (FinalMonicaAudio)
from .speechbrain_final import FinalMonicaAudio

from .wake_word import WakeWordDetector, WakeWordEvent

# Text-to-Speech - Monica's quantum neural lattice voice
try:
    from .monica_tts import MonicaTTS, get_monica_tts
    HAS_MONICA_TTS = True
except ImportError:
    HAS_MONICA_TTS = False
    print("[AUDIO] Monica TTS not available")


class AudioManager:
    """
    Clean Audio Manager for Monica AI.
    Only uses SpeechBrain Personal Voice Recognition.
    """
    
    def __init__(self, config=None):
        """
        Initialize clean audio manager.
        """
        self.config = config or {}
        
        # Audio device
        self.audio = pyaudio.PyAudio() if PYAUDIO_AVAILABLE else None
        
        # Threading and queues
        self.audio_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.is_recording = False
        self.is_processing = False
        
        # Audio streams
        self.input_stream = None
        self.output_stream = None
        
        # Visualization
        self.audio_level = 0.0
        self._level_history = collections.deque(maxlen=50)  # ~0.5s at 100Hz update
        self.audio_buffer = np.array([])
        self.viz_lock = threading.Lock()
        
        # Callbacks
        self.audio_callbacks: List[Callable[[np.ndarray], None]] = []
        self.level_callbacks: List[Callable[[float], None]] = []
        self.audio_data_callbacks: List[Callable[[np.ndarray, float], None]] = []
        self.wake_word_callbacks: List[Callable[[], None]] = []
        
        # Speech recognition (SpeechBrain FinalMonicaAudio)
        self.speech_recognizer = None
        self.vosk_stt = None  # Kept for backward compatibility; not used

        self.last_start_error = None
        
        # Get configured input device
        input_device = getattr(config, 'INPUT_DEVICE_INDEX', None)
        input_device_name = getattr(config, 'INPUT_DEVICE_NAME', None)
        self.input_device_id = input_device
        
        if input_device_name:
            print(f"[AUDIO] Using input device name: {input_device_name}")
        print(f"[AUDIO] Using input device index: {input_device or 'System default'}")
        
        # Initialize SpeechBrain FinalMonicaAudio as the ONLY STT engine
        try:
            print("[AUDIO] Initializing SpeechBrain FinalMonicaAudio (personal STT)...")
            # Pass config through so it can use sample rate / device settings if needed
            # CRITICAL: Store reference to AudioManager in config so SpeechBrain can feed audio queue
            self.config._audio_manager = self
            self.speech_recognizer = FinalMonicaAudio(self.config)
            print("[AUDIO] [OK] SpeechBrain FinalMonicaAudio ready!")
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"[AUDIO] SpeechBrain initialization failed: {e}")
            print(f"[AUDIO] Full error:\n{error_msg}")

            # Save crash report for SpeechBrain initialization failure
            try:
                from monica_ai.crash_reporter import capture_exception
                capture_exception("SpeechBrain Initialization Failed", {
                    "component": "AudioManager",
                    "action": "Initialize FinalMonicaAudio",
                    "input_device": str(input_device or 'default'),
                    "input_device_name": str(input_device_name or ''),
                })
                print("[AUDIO] Crash report saved for SpeechBrain initialization failure")
            except:
                pass

            self.speech_recognizer = None

        if self.speech_recognizer is None:
            print("[AUDIO] WARNING: No speech recognition available!")
            print("[AUDIO] Speech-to-text will NOT work until this is fixed!")
            print("[AUDIO] Check crash_reports/ for details on the initialization failure.")
        
        # Initialize wake word detector
        self.wake_word_detector = WakeWordDetector(
            wake_word=getattr(config, 'WAKE_WORD', 'monica initialize'),
            sensitivity=getattr(config, 'WAKE_WORD_SENSITIVITY', 0.5)
        )
        
        # Recording parameters
        self.sample_rate = getattr(config, 'SAMPLE_RATE', 16000)
        self.channels = getattr(config, 'CHANNELS', 1)
        self.chunk_size = getattr(config, 'CHUNK_SIZE', 1024)
        self.format = getattr(config, 'AUDIO_FORMAT', 'float32')
        
        # Energy threshold for voice activity detection
        self.energy_threshold = getattr(config, 'ENERGY_THRESHOLD', 0.01)
        self.pause_threshold = getattr(config, 'PAUSE_THRESHOLD', 2.0)
        self.phrase_time_limit = getattr(config, 'PHRASE_TIME_LIMIT', 30.0)
        # Anti-barge-in tuning
        self.required_silence_ms = getattr(config, 'REQUIRED_SILENCE_MS', 300)
        
        print(f"[AUDIO] Audio parameters: {self.sample_rate}Hz, {self.channels} channels, {self.chunk_size} chunk")
        print(f"[AUDIO] Voice detection: threshold={self.energy_threshold}, pause={self.pause_threshold}s")
        
        # Start background processing
        self._start_background_processing()
    
    def _start_background_processing(self):
        """Start background audio processing thread"""
        def process_audio():
            while True:
                try:
                    if not self.audio_queue.empty():
                        audio_data = self.audio_queue.get(timeout=1)
                        
                        # Update audio level
                        if len(audio_data) > 0:
                            level = float(np.sqrt(np.mean(audio_data**2)))
                            self.audio_level = level
                            # Keep short history for VAD/anti-barge-in
                            self._level_history.append(level)
                            
                            # Notify level callbacks
                            for callback in self.level_callbacks:
                                try:
                                    callback(level)
                                except Exception as e:
                                    print(f"[AUDIO] Level callback error: {e}")
                        
                        # Notify audio callbacks
                        for callback in self.audio_callbacks:
                            try:
                                callback(audio_data)
                            except Exception as e:
                                print(f"[AUDIO] Audio callback error: {e}")
                        
                        # Store for visualization
                        with self.viz_lock:
                            self.audio_buffer = np.concatenate([self.audio_buffer, audio_data])
                            # Keep only last 5 seconds
                            max_buffer = self.sample_rate * 5
                            if len(self.audio_buffer) > max_buffer:
                                self.audio_buffer = self.audio_buffer[-max_buffer:]
                        
                        # Notify audio data callbacks (for visualization)
                        for callback in self.audio_data_callbacks:
                            try:
                                callback(audio_data, self.audio_level)
                            except Exception as e:
                                print(f"[AUDIO] Data callback error: {e}")
                        
                    else:
                        time.sleep(0.01)
                        
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[AUDIO] Processing error: {e}")
        
        processing_thread = threading.Thread(target=process_audio, daemon=True)
        processing_thread.start()
        print("[AUDIO] Background processing started")
    
    def _on_wake_word_detected(self):
        """Handle wake word detection"""
        print("[AUDIO] Wake word detected!")
        
        # Notify wake word callbacks
        for callback in self.wake_word_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"[AUDIO] Wake word callback error: {e}")
    
    @property
    def is_input_active(self) -> bool:
        """Check if audio input is active"""
        return self.is_recording
    
    def start_input(self) -> bool:
        """Start audio input. Returns True if successful, False otherwise."""
        try:
            success = self.start_recording()
            if not success:
                print(f"[AUDIO] Failed to start input - start_recording returned False")
            return success
        except Exception as e:
            print(f"[AUDIO] Failed to start input: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_input(self):
        """Stop audio input"""
        self.stop_recording()
    
    def start_speech_recognition(self) -> bool:
        """Start speech recognition using SpeechBrain FinalMonicaAudio"""
        print("[AUDIO] start_speech_recognition() called")
        try:
            self.last_start_error = None

            if self.input_stream is not None:
                try:
                    self.stop_recording()
                except Exception:
                    pass

            if self.speech_recognizer and hasattr(self.speech_recognizer, 'start_listening'):
                print("[AUDIO] Calling SpeechBrain start_listening()...")
                self.speech_recognizer.start_listening()
                # Mark recording/listening state for debug report and UI
                self.is_recording = True
                print("[AUDIO] SpeechBrain speech recognition started successfully!")
                return True
            else:
                print(f"[AUDIO] Speech recognition not available - recognizer: {self.speech_recognizer}")
                return False
        except Exception as e:
            self.last_start_error = f"{type(e).__name__}: {e}"
            print(f"[AUDIO] Failed to start speech recognition: {e}")
            import traceback
            traceback.print_exc()

            try:
                from monica_ai.crash_reporter import capture_exception
                capture_exception("Start Voice Recognition Failed", {
                    "component": "AudioManager",
                    "action": "start_speech_recognition",
                    "input_device": str(self.input_device_id),
                    "sample_rate": str(self.sample_rate),
                    "chunk_size": str(self.chunk_size),
                    "details": self.last_start_error,
                })
            except Exception:
                pass
            return False
    
    def start_recognition(self):
        """Start speech recognition (alias)"""
        return self.start_speech_recognition()
    
    def stop_recognition(self):
        """Stop speech recognition"""
        if self.speech_recognizer and hasattr(self.speech_recognizer, 'stop_listening'):
            self.speech_recognizer.stop_listening()
            self.is_recording = False
            print("[AUDIO] Speech recognition stopped")
    
    def start_wake_word_detection(self) -> bool:
        """Start wake word detection"""
        try:
            if self.wake_word_detector:
                self.wake_word_detector.start()
                print("[AUDIO] Wake word detection started")
                return True
            return False
        except Exception as e:
            print(f"[AUDIO] Failed to start wake word detection: {e}")
            return False
    
    def stop_wake_word_detection(self):
        """Stop wake word detection"""
        if self.wake_word_detector:
            self.wake_word_detector.stop()
            print("[AUDIO] Wake word detection stopped")
    
    def recognize_file(self, file_path: str) -> str:
        """Recognize speech from file using SpeechBrain"""
        if self.speech_recognizer and hasattr(self.speech_recognizer, 'recognize_file'):
            return self.speech_recognizer.recognize_file(file_path)
        return ""
    
    def recognize_audio(self, audio_data: np.ndarray) -> str:
        """Recognize speech from audio data using SpeechBrain"""
        if self.speech_recognizer and hasattr(self.speech_recognizer, 'recognize_tensor'):
            import torch
            audio_tensor = torch.from_numpy(audio_data).float()
            return self.speech_recognizer.recognize_tensor(audio_tensor)
        return ""
    
    def start_recording(self) -> bool:
        """Start audio recording. Returns True if successful, False otherwise."""
        if not PYAUDIO_AVAILABLE or self.audio is None:
            print("[AUDIO] PyAudio not available for recording")
            return False

        if self.is_recording:
            print("[AUDIO] Already recording")
            return True  # Already running counts as success

        try:
            self.input_stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.input_device_id,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )

            self.input_stream.start_stream()
            self.is_recording = True
            print("[AUDIO] Recording started")
            return True

        except Exception as e:
            print(f"[AUDIO] Error starting recording: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def stop_recording(self):
        """Stop audio recording"""
        if not self.is_recording:
            return
        
        try:
            if self.input_stream:
                self.input_stream.stop_stream()
                self.input_stream.close()
                self.input_stream = None
            
            self.is_recording = False
            print("[AUDIO] Recording stopped")
            
        except Exception as e:
            print(f"[AUDIO] Error stopping recording: {e}")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback"""
        if status:
            print(f"[AUDIO] Stream status: {status}")
        
        try:
            # Convert bytes to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            # Put in queue for processing
            self.audio_queue.put(audio_data)
            
        except Exception as e:
            print(f"[AUDIO] Audio callback error: {e}")
        
        return (in_data, pyaudio.paContinue)

    # ================= Voice Activity / Anti-barge-in helpers =================
    def is_user_speaking_now(self) -> bool:
        """Heuristic VAD: return True if recent audio level indicates speech.

        Uses a short history of RMS levels. Threshold = max(energy_threshold*1.25, 0.008).
        """
        if not self._level_history:
            return False
        recent = list(self._level_history)
        # Use robust statistic
        avg = float(np.mean(recent))
        thr = max(self.energy_threshold * 1.25, 0.008)
        return avg > thr

    def register_tts_manager(self, tts_manager: Any):
        """Wire this audio manager's VAD to the TTS anti-barge-in callback."""
        try:
            if hasattr(tts_manager, 'set_user_speaking_callback'):
                tts_manager.set_user_speaking_callback(self.is_user_speaking_now)
                print("[AUDIO] [OK] Anti-barge-in wired: TTS will wait for brief silence and stop if you speak")
            else:
                print("[AUDIO] [WARNING] TTS manager has no set_user_speaking_callback")
        except Exception as e:
            print(f"[AUDIO] Failed to wire TTS anti-barge-in: {e}")
    
    def register_audio_callback(self, callback: Callable[[np.ndarray], None]):
        """Register audio data callback"""
        if callback not in self.audio_callbacks:
            self.audio_callbacks.append(callback)
    
    def register_level_callback(self, callback: Callable[[float], None]):
        """Register audio level callback"""
        if callback not in self.level_callbacks:
            self.level_callbacks.append(callback)
    
    def register_audio_data_callback(self, callback: Callable[[np.ndarray, float], None]):
        """Register audio data callback (for visualization)"""
        if callback not in self.audio_data_callbacks:
            self.audio_data_callbacks.append(callback)
    
    def register_wake_word_callback(self, callback: Callable[[], None]):
        """Register wake word detection callback"""
        if callback not in self.wake_word_callbacks:
            self.wake_word_callbacks.append(callback)
    
    def register_speech_callback(self, callback: Callable[[str], None]):
        """Register speech recognition callback"""
        if self.speech_recognizer and hasattr(self.speech_recognizer, 'register_callback'):
            self.speech_recognizer.register_callback(callback)
            print("[AUDIO] [OK] Speech callback registered with SpeechBrain")
        else:
            print("[AUDIO] [WARNING] No speech recognizer available for callback registration")
    
    def get_audio_level(self) -> float:
        """Get current audio level"""
        return self.audio_level
    
    def get_audio_buffer(self, duration: float = 5.0) -> np.ndarray:
        """Get recent audio buffer"""
        with self.viz_lock:
            samples = int(self.sample_rate * duration)
            if len(self.audio_buffer) > samples:
                return self.audio_buffer[-samples:]
            return self.audio_buffer.copy()
    
    def is_speechbrain_ready(self) -> bool:
        """Check if speech recognition is ready"""
        if self.speech_recognizer and hasattr(self.speech_recognizer, 'is_ready'):
            return self.speech_recognizer.is_ready()
        return False
    
    def wait_until_ready(self, timeout: int = 180) -> bool:
        """Wait until speech recognition is ready"""
        if self.speech_recognizer and hasattr(self.speech_recognizer, 'wait_until_ready'):
            return self.speech_recognizer.wait_until_ready(timeout)
        return False
    
    def get_status(self) -> str:
        """Get system status"""
        if self.is_speechbrain_ready():
            return "Speech Recognition Ready"
        elif self.speech_recognizer:
            return "Loading..."
        else:
            return "No Speech Recognition"
    
    @property
    def is_listening(self) -> bool:
        """Check if currently listening"""
        return self.is_recording
    
    def stop_speech_recognition(self):
        """Stop speech recognition (alias for stop_recognition)"""
        self.stop_recognition()
    
    def stop(self):
        """Stop all audio (alias for cleanup)"""
        self.cleanup()
    
    def list_input_devices(self) -> list:
        """List available input devices"""
        devices = []
        if PYAUDIO_AVAILABLE and self.audio:
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': info['name'],
                        'channels': info['maxInputChannels']
                    })
        return devices
    
    def list_output_devices(self) -> list:
        """List available output devices"""
        devices = []
        if PYAUDIO_AVAILABLE and self.audio:
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['maxOutputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': info['name'],
                        'channels': info['maxOutputChannels']
                    })
        return devices
    
    def set_input_device(self, device_index: int):
        """Set the input device by index"""
        # Stop current recording if active
        was_recording = self.is_recording
        if was_recording:
            self.stop_recording()
        
        # Update device index
        self.input_device_id = device_index
        
        # Get device name for logging
        device_name = "Unknown"
        if PYAUDIO_AVAILABLE and self.audio:
            try:
                info = self.audio.get_device_info_by_index(device_index)
                device_name = info.get('name', 'Unknown')
            except:
                pass
        
        print(f"[AUDIO] Input device changed to: {device_name} (index {device_index})")
        
        # Restart recording if it was active
        if was_recording:
            self.start_recording()
        
        return True
    
    def set_output_device(self, device_index: int):
        """Set the output device by index"""
        # Note: Output device is typically handled by TTS, not AudioManager
        print(f"[AUDIO] Output device set to index {device_index}")
        return True
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_recording()
        self.stop_recognition()
        
        if self.audio:
            self.audio.terminate()
        
        print("[AUDIO] Cleaned up")
    
    # ==================== TTS Methods ====================
    
    def speak(self, text: str, blocking: bool = False, callback=None) -> bool:
        """
        Speak text using Monica's quantum neural lattice voice.
        
        Args:
            text: Text to speak
            blocking: If True, wait for speech to complete
            callback: Optional callback when speech completes
        
        Returns:
            True if speech started successfully
        """
        if not HAS_MONICA_TTS:
            print(f"[AUDIO] TTS not available. Would say: {text}")
            return False
        
        try:
            tts = get_monica_tts()
            return tts.speak(text, blocking=blocking, callback=callback)
        except Exception as e:
            print(f"[AUDIO] TTS error: {e}")
            return False
    
    def synthesize_speech(self, text: str, output_path: str = None) -> str:
        """
        Synthesize speech to a file.
        
        Args:
            text: Text to synthesize
            output_path: Optional output file path
        
        Returns:
            Path to the generated audio file
        """
        if not HAS_MONICA_TTS:
            print(f"[AUDIO] TTS not available")
            return None
        
        try:
            tts = get_monica_tts()
            return tts.synthesize(text, output_path=output_path)
        except Exception as e:
            print(f"[AUDIO] TTS synthesis error: {e}")
            return None
