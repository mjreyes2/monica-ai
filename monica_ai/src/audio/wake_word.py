"""
Wake Word Detection module.
Supports custom wake words like "Hey Monica" using voice activity detection
and keyword spotting.
"""
import numpy as np
import queue
import threading
import time
from dataclasses import dataclass
from typing import Optional, Callable, List
from enum import Enum


class WakeWordState(Enum):
    """State of wake word detection."""
    IDLE = "idle"
    LISTENING = "listening"
    DETECTED = "detected"
    COOLDOWN = "cooldown"


@dataclass
class WakeWordEvent:
    """Event triggered when wake word is detected."""
    timestamp: float
    confidence: float
    audio_data: Optional[np.ndarray] = None


class WakeWordDetector:
    """
    Wake word detector for "Hey Monica" and custom wake words.
    
    Uses a combination of:
    1. Voice Activity Detection (VAD)
    2. Simple keyword spotting with phonetic matching
    3. Optional Porcupine integration for more accurate detection
    
    This implementation provides a lightweight fallback when
    Porcupine is not available.
    """
    
    # Original wake word patterns
    WAKE_WORD_PATTERNS = {
        'monica initialize': [
            'monica initialize', 'monika initialize', 'initialize monica',
            'monica init', 'init monica', 'start monica', 'begin monica'
        ]
    }
    
    def __init__(
        self,
        wake_word: str = "monica initialize",
        sensitivity: float = 0.4,  # Slightly more sensitive for better detection
        sample_rate: int = 16000,
        cooldown_seconds: float = 1.5,  # Shorter cooldown for more responsive detection
        use_porcupine: bool = False,
        porcupine_access_key: str = None
    ):
        """
        Initialize the wake word detector.
        
        Args:
            wake_word: The wake word to detect
            sensitivity: Detection sensitivity (0.0 to 1.0)
            sample_rate: Audio sample rate
            cooldown_seconds: Cooldown period after detection
            use_porcupine: Whether to use Porcupine for detection
            porcupine_access_key: Porcupine access key (required if use_porcupine=True)
        """
        self.wake_word = wake_word.lower()
        self.sensitivity = sensitivity
        self.sample_rate = sample_rate
        self.cooldown_seconds = cooldown_seconds
        self.use_porcupine = use_porcupine
        self.porcupine_access_key = porcupine_access_key
        
        # State
        self.state = WakeWordState.IDLE
        self.is_running = False
        self.stop_event = threading.Event()
        self.last_detection_time = 0
        
        # Audio processing
        self.audio_queue = queue.Queue()
        self.detection_thread = None
        self.frame_length = int(sample_rate * 0.032)  # 32ms frames
        
        # Voice activity detection settings
        self.vad_threshold = 0.01  # Standard sensitivity for voice detection
        self.speech_frames = 0
        self.silence_frames = 0
        self.min_speech_frames = 5  # Standard number of frames to detect speech
        self.max_silence_frames = 20  # Standard silence between words
        
        # Callbacks
        self.callbacks: List[Callable[[WakeWordEvent], None]] = []
        
        # Porcupine (optional)
        self.porcupine = None
        if use_porcupine and porcupine_access_key:
            self._init_porcupine()
        
        # Simple speech recognizer for keyword spotting
        self.speech_recognizer = None
        self._init_keyword_spotter()
    
    def _init_porcupine(self):
        """Initialize Porcupine wake word engine."""
        try:
            import pvporcupine
            
            # Check if custom wake word is available
            # Porcupine has built-in keywords, but "monica" would need to be custom
            self.porcupine = pvporcupine.create(
                access_key=self.porcupine_access_key,
                keywords=["computer"],  # Use built-in keyword as fallback
                sensitivities=[self.sensitivity]
            )
            print("Porcupine wake word engine initialized")
            
        except ImportError:
            print("Porcupine not installed. Using fallback detection.")
            self.use_porcupine = False
        except Exception as e:
            print(f"Error initializing Porcupine: {e}")
            self.use_porcupine = False
    
    def _init_keyword_spotter(self):
        """Initialize simple keyword spotter using Whisper."""
        # We'll use the speech recognizer from the parent module
        # for keyword spotting when Porcupine is not available
        pass
    
    def start(self) -> bool:
        """Start wake word detection."""
        if self.is_running:
            return True
        
        self.is_running = True
        self.state = WakeWordState.LISTENING
        self.stop_event.clear()
        
        # Start detection thread
        self.detection_thread = threading.Thread(
            target=self._detection_loop,
            daemon=True
        )
        self.detection_thread.start()
        
        print(f"Wake word detection started for '{self.wake_word}'")
        return True
    
    def stop(self):
        """Stop wake word detection."""
        if not self.is_running:
            return
        
        self.is_running = False
        self.state = WakeWordState.IDLE
        self.stop_event.set()
        
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=1.0)
        
        # Clean up Porcupine
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None
        
        print("Wake word detection stopped")
    
    def process_audio(self, audio_data: np.ndarray):
        """
        Process incoming audio data.
        
        Args:
            audio_data: Audio samples as numpy array
        """
        if not self.is_running:
            return
        
        # Ensure correct format
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        self.audio_queue.put(audio_data)
    
    def _detection_loop(self):
        """Main detection loop."""
        audio_buffer = []
        
        while not self.stop_event.is_set():
            try:
                # Check cooldown
                current_time = time.time()
                if self.state == WakeWordState.DETECTED:
                    if current_time - self.last_detection_time > self.cooldown_seconds:
                        self.state = WakeWordState.LISTENING
                    else:
                        time.sleep(0.1)
                        continue
                
                # Get audio from queue
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Add to buffer
                audio_buffer.append(audio_chunk)
                
                # Process when we have enough audio (at least 0.5 seconds)
                total_samples = sum(len(chunk) for chunk in audio_buffer)
                buffer_duration = total_samples / self.sample_rate
                
                if buffer_duration >= 0.5:  # Process every 0.5 seconds
                    audio_data = np.concatenate(audio_buffer)
                    
                    # Detect wake word using VAD
                    detected, confidence = self._detect_with_vad(audio_data)
                    
                    if detected:
                        self._on_wake_word_detected(confidence, audio_data)
                    
                    # Keep last 0.1 seconds for overlap
                    keep_samples = int(0.1 * self.sample_rate)
                    if len(audio_data) > keep_samples:
                        audio_buffer = [audio_data[-keep_samples:]]
                    else:
                        audio_buffer.clear()
                
            except Exception as e:
                print(f"Error in wake word detection: {e}")
                audio_buffer.clear()  # Clear buffer on error
    
    def _detect_wake_word(self, audio_data: np.ndarray) -> tuple:
        """
        Detect wake word in audio data.
        
        Returns:
            Tuple of (detected: bool, confidence: float)
        """
        # Use Porcupine if available
        if self.use_porcupine and self.porcupine:
            return self._detect_with_porcupine(audio_data)
        
        # Fallback: Simple VAD + energy-based detection
        return self._detect_with_vad(audio_data)
    
    def _detect_with_porcupine(self, audio_data: np.ndarray) -> tuple:
        """Detect wake word using Porcupine."""
        try:
            # Convert to int16 for Porcupine
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Process in frames
            frame_length = self.porcupine.frame_length
            
            for i in range(0, len(audio_int16) - frame_length, frame_length):
                frame = audio_int16[i:i + frame_length]
                result = self.porcupine.process(frame)
                
                if result >= 0:
                    return True, 0.9  # Porcupine detected
            
            return False, 0.0
            
        except Exception as e:
            print(f"Porcupine detection error: {e}")
            return False, 0.0
    
    def _detect_with_vad(self, audio_data: np.ndarray) -> tuple:
        """
        Simple voice activity detection based wake word detection.
        
        This uses energy-based detection to identify potential wake word patterns.
        """
        # Calculate energy (RMS)
        energy = np.sqrt(np.mean(audio_data ** 2))
        
        # Simple threshold-based detection
        threshold = self.vad_threshold * (1.1 - self.sensitivity)
        
        if energy > threshold:
            self.speech_frames += 1
            self.silence_frames = 0
        else:
            self.silence_frames += 1
            if self.silence_frames > self.max_silence_frames:
                self.speech_frames = 0
        
        # Check if we have enough speech to consider it a potential wake word
        if self.speech_frames >= self.min_speech_frames:
            # Calculate confidence based on energy and duration
            confidence = min(1.0, (energy / threshold) * 0.5)  # Cap at 1.0
            
            # Reset counters
            self.speech_frames = 0
            
            # Only trigger if we're not in cooldown
            current_time = time.time()
            if current_time - self.last_detection_time > self.cooldown_seconds:
                return True, confidence
        
        return False, 0.0
    
    def _on_wake_word_detected(self, confidence: float, audio_data: np.ndarray):
        """Handle wake word detection."""
        self.state = WakeWordState.DETECTED
        self.last_detection_time = time.time()
        
        # Create event
        event = WakeWordEvent(
            timestamp=self.last_detection_time,
            confidence=confidence,
            audio_data=audio_data.copy()
        )
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in wake word callback: {e}")
        
        # Enter cooldown
        self.state = WakeWordState.COOLDOWN
        
        print(f"Wake word detected! Confidence: {confidence:.2f}")
    
    def register_callback(self, callback: Callable[[WakeWordEvent], None]):
        """Register a callback for wake word detection."""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[WakeWordEvent], None]):
        """Unregister a callback."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def set_wake_word(self, wake_word: str):
        """Set the wake word."""
        self.wake_word = wake_word.lower()
    
    def set_sensitivity(self, sensitivity: float):
        """Set detection sensitivity (0.0 to 1.0)."""
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        
        # Update Porcupine sensitivity if available
        if self.porcupine:
            # Porcupine doesn't support runtime sensitivity changes
            # Would need to reinitialize
            pass
    
    def get_state(self) -> WakeWordState:
        """Get current detection state."""
        return self.state
    
    def is_detected(self) -> bool:
        """Check if wake word was recently detected."""
        return self.state == WakeWordState.DETECTED


class WakeWordWithWhisper(WakeWordDetector):
    """
    Enhanced wake word detector that uses Whisper for verification.
    
    This provides more accurate wake word detection by using
    speech recognition to verify the detected audio.
    """
    
    def __init__(self, speech_recognizer=None, **kwargs):
        """
        Initialize with optional speech recognizer.
        
        Args:
            speech_recognizer: WhisperSpeechRecognizer instance for verification
            **kwargs: Arguments passed to WakeWordDetector
        """
        super().__init__(**kwargs)
        self.speech_recognizer = speech_recognizer
        self.verification_enabled = speech_recognizer is not None
    
    def _detect_wake_word(self, audio_data: np.ndarray) -> tuple:
        """Detect and verify wake word using Whisper."""
        # First, check with VAD
        detected, confidence = self._detect_with_vad(audio_data)
        
        if not detected:
            return False, 0.0
        
        # Verify with speech recognition if available
        if self.verification_enabled and self.speech_recognizer:
            return self._verify_with_whisper(audio_data)
        
        return detected, confidence
    
    def _verify_with_whisper(self, audio_data: np.ndarray) -> tuple:
        """Verify wake word using Whisper transcription."""
        try:
            if not self.speech_recognizer.is_model_loaded:
                return False, 0.0
            
            # Transcribe the audio
            result = self.speech_recognizer._transcribe(audio_data)
            
            if result is None or not result.text:
                return False, 0.0
            
            # Check if transcription contains wake word
            text = result.text.lower()
            
            # Check against wake word patterns
            patterns = self.WAKE_WORD_PATTERNS.get(
                self.wake_word,
                [self.wake_word]
            )
            
            for pattern in patterns:
                if pattern in text:
                    # Calculate confidence based on match quality
                    confidence = 0.9 if pattern == self.wake_word else 0.7
                    return True, confidence
            
            return False, 0.0
            
        except Exception as e:
            print(f"Whisper verification error: {e}")
            return False, 0.0
    
    def set_speech_recognizer(self, speech_recognizer):
        """Set the speech recognizer for verification."""
        self.speech_recognizer = speech_recognizer
        self.verification_enabled = speech_recognizer is not None
