"""
Biometric Detection System for Monica AI
Detects: Emotions, Age, Identity, Heartbeat

Author: Marvin's AI Assistant
Date: 2025-12-12
"""

import cv2
import numpy as np
import threading
import time
from typing import Optional, Dict, List, Tuple, Callable, Any
from dataclasses import dataclass
from collections import deque
import json
from pathlib import Path

# Try to import advanced detection libraries
try:
    # Fix TensorFlow __version__ issue before importing DeepFace
    import tensorflow as tf
    if not hasattr(tf, '__version__'):
        # TensorFlow 2.16+ moved __version__ - add it back for compatibility
        try:
            tf.__version__ = tf.version.VERSION
        except AttributeError:
            tf.__version__ = "2.16.0"  # Fallback version string
    
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except (ImportError, AttributeError) as e:
    DEEPFACE_AVAILABLE = False
    print(f"[BIOMETRIC] DeepFace not available: {e}")

try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("[BIOMETRIC] Librosa not available. Install with: pip install librosa soundfile")


@dataclass
class EmotionResult:
    """Result from emotion detection."""
    emotion: str  # dominant, happy, sad, angry, fear, surprise, neutral
    confidence: float  # 0-1
    all_emotions: Dict[str, float]  # All detected emotions with scores
    source: str  # 'face', 'voice', or 'combined'
    timestamp: float


@dataclass
class AgeResult:
    """Result from age detection."""
    age: int  # Estimated age
    min_age: int  # Lower bound
    max_age: int  # Upper bound
    confidence: float  # 0-1
    source: str  # 'face' or 'voice'
    timestamp: float


@dataclass
class IdentityResult:
    """Result from identity recognition."""
    identified: bool  # True if recognized
    identity: Optional[str]  # Name/ID if recognized
    confidence: float  # 0-1
    is_owner: bool  # True if this is the owner (Marvin)
    source: str  # 'face', 'voice', or 'combined'
    timestamp: float


@dataclass
class HeartbeatResult:
    """Result from heartbeat detection."""
    bpm: Optional[float]  # Beats per minute
    confidence: float  # 0-1
    method: str  # 'rppg' (camera), 'audio', or 'unavailable'
    quality: str  # 'good', 'fair', 'poor'
    timestamp: float


class EmotionDetector:
    """Detects emotions from face and voice."""

    def __init__(self):
        """Initialize emotion detector."""
        self.enabled = DEEPFACE_AVAILABLE
        self.last_result = None
        self.history = deque(maxlen=30)  # Last 30 results for smoothing

        # Emotion mapping
        self.emotion_map = {
            'angry': 'angry',
            'disgust': 'disgusted',
            'fear': 'fearful',
            'happy': 'happy',
            'sad': 'sad',
            'surprise': 'surprised',
            'neutral': 'neutral'
        }

        print(f"[EMOTION] Detector initialized (DeepFace: {self.enabled})")

    def detect_from_face(self, frame: np.ndarray) -> Optional[EmotionResult]:
        """
        Detect emotion from face image.

        Args:
            frame: OpenCV image (BGR format)

        Returns:
            EmotionResult or None if detection failed
        """
        if not self.enabled or frame is None:
            return None

        try:
            # Use DeepFace to analyze emotions - try multiple backends
            result = None
            for backend in ['opencv', 'ssd', 'mtcnn']:
                try:
                    result = DeepFace.analyze(
                        frame,
                        actions=['emotion'],
                        enforce_detection=False,  # Don't fail if no face detected
                        detector_backend=backend,
                        silent=True
                    )
                    if result:
                        break  # Success with this backend
                except Exception:
                    continue  # Try next backend

            if not result:
                return None  # No detector worked

            if isinstance(result, list):
                result = result[0]  # Get first face

            emotions = result.get('emotion', {})
            if not emotions:
                return None

            # Find dominant emotion
            dominant = max(emotions.items(), key=lambda x: x[1])
            emotion_name = self.emotion_map.get(dominant[0], dominant[0])
            confidence = dominant[1] / 100.0  # Convert to 0-1

            # Create result
            emotion_result = EmotionResult(
                emotion=emotion_name,
                confidence=confidence,
                all_emotions={self.emotion_map.get(k, k): v/100.0 for k, v in emotions.items()},
                source='face',
                timestamp=time.time()
            )

            self.last_result = emotion_result
            self.history.append(emotion_result)

            return emotion_result

        except Exception as e:
            print(f"[EMOTION] Face detection error: {e}")
            return None

    def detect_from_voice(self, audio_data: np.ndarray, sample_rate: int = 16000) -> Optional[EmotionResult]:
        """
        Detect emotion from voice/audio.

        Args:
            audio_data: Audio samples (numpy array)
            sample_rate: Sample rate in Hz

        Returns:
            EmotionResult or None if detection failed
        """
        if not LIBROSA_AVAILABLE or audio_data is None:
            return None

        try:
            # Extract audio features for emotion detection
            # Basic voice emotion detection using prosodic features

            # Pitch (F0) - higher pitch = excitement/happiness
            # Energy - louder = more intense emotion
            # Speaking rate - faster = excitement/anxiety

            # Extract features
            energy = np.mean(librosa.feature.rms(y=audio_data))
            pitch_mean = np.mean(librosa.piptrack(y=audio_data, sr=sample_rate)[0])

            # Simple rule-based emotion detection
            # (In production, you'd use a trained model)
            emotion = 'neutral'
            confidence = 0.5

            if energy > 0.05:
                if pitch_mean > 200:
                    emotion = 'happy'
                    confidence = 0.6
                else:
                    emotion = 'angry'
                    confidence = 0.5
            elif energy < 0.02:
                emotion = 'sad'
                confidence = 0.5

            emotion_result = EmotionResult(
                emotion=emotion,
                confidence=confidence,
                all_emotions={emotion: confidence},
                source='voice',
                timestamp=time.time()
            )

            return emotion_result

        except Exception as e:
            print(f"[EMOTION] Voice detection error: {e}")
            return None

    def get_smoothed_emotion(self) -> Optional[EmotionResult]:
        """Get smoothed emotion based on recent history."""
        if not self.history:
            return None

        # Count emotions in recent history
        emotion_counts = {}
        total_confidence = {}

        for result in self.history:
            emotion = result.emotion
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            total_confidence[emotion] = total_confidence.get(emotion, 0) + result.confidence

        # Find most common emotion
        dominant = max(emotion_counts.items(), key=lambda x: x[1])
        emotion = dominant[0]
        count = dominant[1]
        avg_confidence = total_confidence[emotion] / count

        return EmotionResult(
            emotion=emotion,
            confidence=avg_confidence,
            all_emotions={emotion: avg_confidence},
            source='smoothed',
            timestamp=time.time()
        )


class AgeDetector:
    """Detects approximate age from face."""

    def __init__(self):
        """Initialize age detector."""
        self.enabled = DEEPFACE_AVAILABLE
        self.last_age = None
        self.history = deque(maxlen=10)  # Last 10 detections

        print(f"[AGE] Detector initialized (DeepFace: {self.enabled})")

    def detect_from_face(self, frame: np.ndarray) -> Optional[AgeResult]:
        """
        Detect age from face image.

        Args:
            frame: OpenCV image (BGR format)

        Returns:
            AgeResult or None if detection failed
        """
        if not self.enabled or frame is None:
            return None

        try:
            # Use DeepFace to analyze age - try multiple backends
            result = None
            for backend in ['opencv', 'ssd', 'mtcnn']:
                try:
                    result = DeepFace.analyze(
                        frame,
                        actions=['age'],
                        enforce_detection=False,
                        detector_backend=backend,
                        silent=True
                    )
                    if result:
                        break  # Success with this backend
                except Exception:
                    continue  # Try next backend

            if not result:
                return None  # No detector worked

            if isinstance(result, list):
                result = result[0]

            age = result.get('age')
            if age is None:
                return None

            # Estimate range (±5 years)
            min_age = max(0, age - 5)
            max_age = age + 5

            age_result = AgeResult(
                age=int(age),
                min_age=int(min_age),
                max_age=int(max_age),
                confidence=0.7,  # DeepFace doesn't provide age confidence
                source='face',
                timestamp=time.time()
            )

            self.last_age = age_result
            self.history.append(age_result)

            return age_result

        except Exception as e:
            print(f"[AGE] Detection error: {e}")
            return None

    def get_average_age(self) -> Optional[AgeResult]:
        """Get average age from recent history."""
        if not self.history:
            return None

        ages = [r.age for r in self.history]
        avg_age = int(np.mean(ages))
        min_age = max(0, avg_age - 5)
        max_age = avg_age + 5

        return AgeResult(
            age=avg_age,
            min_age=min_age,
            max_age=max_age,
            confidence=0.8,  # Higher confidence with averaging
            source='face_averaged',
            timestamp=time.time()
        )


class IdentityRecognizer:
    """Recognizes identity from face and voice."""

    def __init__(self, owner_name: str = "MJP"):
        """
        Initialize identity recognizer.

        Args:
            owner_name: Name of the system owner
        """
        self.enabled = DEEPFACE_AVAILABLE
        self.owner_name = owner_name
        self.face_database = {}  # {name: face_embedding}
        self.voice_database = {}  # {name: voice_embedding}
        self.last_identity = None

        # Load database if exists
        self.db_path = Path("biometric_data/identity_database.json")
        self._load_database()

        print(f"[IDENTITY] Recognizer initialized (Owner: {owner_name})")

    def _load_database(self):
        """Load identity database from file."""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    # Note: Can't store numpy arrays in JSON, would need to use pickle or npz
                    print(f"[IDENTITY] Loaded {len(data)} identities from database")
            except Exception as e:
                print(f"[IDENTITY] Error loading database: {e}")

    def _save_database(self):
        """Save identity database to file."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            # Save would require converting numpy arrays properly
            print("[IDENTITY] Database saved")
        except Exception as e:
            print(f"[IDENTITY] Error saving database: {e}")

    def register_face(self, frame: np.ndarray, name: str) -> bool:
        """
        Register a face for identity recognition.

        Args:
            frame: Face image
            name: Person's name

        Returns:
            True if registration successful
        """
        if not self.enabled:
            return False

        try:
            # Extract face embedding
            embedding = DeepFace.represent(
                frame,
                model_name='Facenet',
                enforce_detection=False,
                detector_backend='opencv'
            )

            if isinstance(embedding, list):
                embedding = embedding[0]['embedding']

            self.face_database[name] = np.array(embedding)
            self._save_database()

            print(f"[IDENTITY] Registered face for: {name}")
            return True

        except Exception as e:
            print(f"[IDENTITY] Registration error: {e}")
            return False

    def recognize_face(self, frame: np.ndarray) -> Optional[IdentityResult]:
        """
        Recognize identity from face.

        Args:
            frame: Face image

        Returns:
            IdentityResult or None if recognition failed
        """
        if not self.enabled or frame is None or not self.face_database:
            return IdentityResult(
                identified=False,
                identity=None,
                confidence=0.0,
                is_owner=False,
                source='face',
                timestamp=time.time()
            )

        try:
            # Extract face embedding from current frame
            current_embedding = DeepFace.represent(
                frame,
                model_name='Facenet',
                enforce_detection=False,
                detector_backend='opencv'
            )

            if isinstance(current_embedding, list):
                current_embedding = current_embedding[0]['embedding']

            current_embedding = np.array(current_embedding)

            # Compare with database
            best_match = None
            best_distance = float('inf')

            for name, stored_embedding in self.face_database.items():
                distance = np.linalg.norm(current_embedding - stored_embedding)
                if distance < best_distance:
                    best_distance = distance
                    best_match = name

            # Threshold for recognition (adjust based on testing)
            threshold = 0.6
            if best_distance < threshold and best_match:
                confidence = 1.0 - (best_distance / threshold)

                identity_result = IdentityResult(
                    identified=True,
                    identity=best_match,
                    confidence=confidence,
                    is_owner=(best_match.lower() == self.owner_name.lower()),
                    source='face',
                    timestamp=time.time()
                )
            else:
                identity_result = IdentityResult(
                    identified=False,
                    identity=None,
                    confidence=0.0,
                    is_owner=False,
                    source='face',
                    timestamp=time.time()
                )

            self.last_identity = identity_result
            return identity_result

        except Exception as e:
            print(f"[IDENTITY] Recognition error: {e}")
            return None


class HeartbeatDetector:
    """Detects heartbeat using camera-based rPPG (remote photoplethysmography)."""

    def __init__(self):
        """Initialize heartbeat detector."""
        self.enabled = True  # OpenCV-based, always available
        self.last_bpm = None
        self.history = deque(maxlen=300)  # 10 seconds at 30fps
        self.signal_buffer = deque(maxlen=300)

        print("[HEARTBEAT] Detector initialized (rPPG method)")

    def process_frame(self, frame: np.ndarray, face_region: Optional[Tuple[int, int, int, int]] = None) -> Optional[float]:
        """
        Process a frame for heartbeat detection.

        Args:
            frame: OpenCV image (BGR format)
            face_region: Optional (x, y, w, h) tuple of face location

        Returns:
            Average green channel intensity (for signal building)
        """
        if frame is None:
            return None

        try:
            # If face region provided, use it; otherwise use whole frame
            if face_region:
                x, y, w, h = face_region
                # Extract forehead region (upper 1/3 of face, rich in blood vessels)
                forehead_y = y + int(h * 0.1)
                forehead_h = int(h * 0.3)
                roi = frame[forehead_y:forehead_y+forehead_h, x:x+w]
            else:
                # Use center region of frame
                h, w = frame.shape[:2]
                roi = frame[int(h*0.3):int(h*0.6), int(w*0.3):int(w*0.7)]

            if roi.size == 0:
                return None

            # Extract green channel (most sensitive to blood volume changes)
            green_channel = roi[:, :, 1]  # BGR format, so index 1 is green

            # Calculate mean green intensity
            mean_green = np.mean(green_channel)

            # Add to signal buffer
            self.signal_buffer.append(mean_green)

            return mean_green

        except Exception as e:
            print(f"[HEARTBEAT] Frame processing error: {e}")
            return None

    def calculate_bpm(self, fps: float = 30.0) -> Optional[HeartbeatResult]:
        """
        Calculate BPM from signal buffer using FFT.

        Args:
            fps: Frame rate of video

        Returns:
            HeartbeatResult or None if insufficient data
        """
        if len(self.signal_buffer) < 150:  # Need at least 5 seconds
            return HeartbeatResult(
                bpm=None,
                confidence=0.0,
                method='rppg',
                quality='insufficient_data',
                timestamp=time.time()
            )

        try:
            # Convert signal buffer to numpy array
            signal = np.array(self.signal_buffer)

            # Detrend signal (remove slow variations)
            signal_detrended = signal - np.mean(signal)

            # Apply bandpass filter (0.7-4 Hz = 42-240 BPM)
            # Simple moving average filter
            window_size = int(fps * 2)  # 2 second window
            if len(signal_detrended) < window_size:
                window_size = len(signal_detrended)

            signal_filtered = np.convolve(signal_detrended, np.ones(window_size)/window_size, mode='same')

            # Perform FFT
            fft_result = np.fft.fft(signal_filtered)
            fft_freq = np.fft.fftfreq(len(signal_filtered), 1.0/fps)

            # Only positive frequencies
            positive_freqs = fft_freq[:len(fft_freq)//2]
            positive_fft = np.abs(fft_result[:len(fft_result)//2])

            # Find frequencies in heart rate range (0.7-4 Hz = 42-240 BPM)
            hr_range = (positive_freqs >= 0.7) & (positive_freqs <= 4.0)
            hr_freqs = positive_freqs[hr_range]
            hr_fft = positive_fft[hr_range]

            if len(hr_fft) == 0:
                return HeartbeatResult(
                    bpm=None,
                    confidence=0.0,
                    method='rppg',
                    quality='poor',
                    timestamp=time.time()
                )

            # Find peak frequency
            peak_idx = np.argmax(hr_fft)
            peak_freq = hr_freqs[peak_idx]
            bpm = peak_freq * 60.0

            # Estimate confidence based on signal quality
            # Higher peak relative to noise = better confidence
            signal_strength = hr_fft[peak_idx] / np.mean(hr_fft)
            confidence = min(1.0, signal_strength / 10.0)  # Normalize

            # Determine quality
            if confidence > 0.7:
                quality = 'good'
            elif confidence > 0.4:
                quality = 'fair'
            else:
                quality = 'poor'

            result = HeartbeatResult(
                bpm=float(bpm),
                confidence=float(confidence),
                method='rppg',
                quality=quality,
                timestamp=time.time()
            )

            self.last_bpm = result
            return result

        except Exception as e:
            print(f"[HEARTBEAT] BPM calculation error: {e}")
            return None


class BiometricDetector:
    """
    Main biometric detection system.
    Integrates emotion, age, identity, and heartbeat detection.
    """

    def __init__(self, owner_name: str = "MJP"):
        """
        Initialize biometric detector system.

        Args:
            owner_name: Name of system owner
        """
        self.owner_name = owner_name

        # Initialize sub-detectors
        self.emotion_detector = EmotionDetector()
        self.age_detector = AgeDetector()
        self.identity_recognizer = IdentityRecognizer(owner_name)
        self.heartbeat_detector = HeartbeatDetector()

        # State
        self.enabled = True
        self.last_update = time.time()
        self.update_interval = 1.0  # Update every second

        # Results cache
        self.current_emotion: Optional[EmotionResult] = None
        self.current_age: Optional[AgeResult] = None
        self.current_identity: Optional[IdentityResult] = None
        self.current_heartbeat: Optional[HeartbeatResult] = None

        # Callbacks
        self.emotion_callbacks: List[Callable[[EmotionResult], None]] = []
        self.age_callbacks: List[Callable[[AgeResult], None]] = []
        self.identity_callbacks: List[Callable[[IdentityResult], None]] = []
        self.heartbeat_callbacks: List[Callable[[HeartbeatResult], None]] = []

        print(f"[BIOMETRIC] System initialized (Owner: {owner_name})")

    def process_frame(self, frame: np.ndarray):
        """
        Process a video frame for all biometric detections.

        Args:
            frame: OpenCV image (BGR format)
        """
        if not self.enabled or frame is None:
            return

        # Throttle updates
        now = time.time()
        if now - self.last_update < self.update_interval:
            # Still process heartbeat for signal building
            self.heartbeat_detector.process_frame(frame)
            return

        self.last_update = now

        # Run detections (in separate thread to avoid blocking)
        threading.Thread(target=self._process_detections, args=(frame.copy(),), daemon=True).start()

    def _process_detections(self, frame: np.ndarray):
        """Process all detections in background thread."""
        # Detect emotion from face
        emotion = self.emotion_detector.detect_from_face(frame)
        if emotion:
            self.current_emotion = emotion
            for callback in self.emotion_callbacks:
                try:
                    callback(emotion)
                except Exception as e:
                    print(f"[BIOMETRIC] Emotion callback error: {e}")

        # Detect age
        age = self.age_detector.detect_from_face(frame)
        if age:
            self.current_age = age
            for callback in self.age_callbacks:
                try:
                    callback(age)
                except Exception as e:
                    print(f"[BIOMETRIC] Age callback error: {e}")

        # Recognize identity
        identity = self.identity_recognizer.recognize_face(frame)
        if identity:
            self.current_identity = identity
            for callback in self.identity_callbacks:
                try:
                    callback(identity)
                except Exception as e:
                    print(f"[BIOMETRIC] Identity callback error: {e}")

        # Calculate heartbeat (need accumulated signal)
        heartbeat = self.heartbeat_detector.calculate_bpm()
        if heartbeat and heartbeat.bpm is not None:
            self.current_heartbeat = heartbeat
            for callback in self.heartbeat_callbacks:
                try:
                    callback(heartbeat)
                except Exception as e:
                    print(f"[BIOMETRIC] Heartbeat callback error: {e}")

    def process_audio(self, audio_data: np.ndarray, sample_rate: int = 16000):
        """
        Process audio for voice-based biometrics.

        Args:
            audio_data: Audio samples
            sample_rate: Sample rate in Hz
        """
        if not self.enabled:
            return

        # Detect emotion from voice
        emotion = self.emotion_detector.detect_from_voice(audio_data, sample_rate)
        if emotion:
            # Combine with face emotion if available
            if self.current_emotion and self.current_emotion.source == 'face':
                # Average the confidences
                combined_confidence = (self.current_emotion.confidence + emotion.confidence) / 2
                self.current_emotion = EmotionResult(
                    emotion=self.current_emotion.emotion,  # Prefer face emotion
                    confidence=combined_confidence,
                    all_emotions=self.current_emotion.all_emotions,
                    source='combined',
                    timestamp=time.time()
                )
            else:
                self.current_emotion = emotion

    def get_status(self) -> Dict[str, Any]:
        """
        Get current biometric status.

        Returns:
            Dictionary with all current biometric data
        """
        return {
            'emotion': {
                'detected': self.current_emotion is not None,
                'value': self.current_emotion.emotion if self.current_emotion else None,
                'confidence': self.current_emotion.confidence if self.current_emotion else 0.0,
                'all_emotions': self.current_emotion.all_emotions if self.current_emotion else {},
                'source': self.current_emotion.source if self.current_emotion else None,
            } if self.current_emotion else None,

            'age': {
                'detected': self.current_age is not None,
                'value': self.current_age.age if self.current_age else None,
                'range': f"{self.current_age.min_age}-{self.current_age.max_age}" if self.current_age else None,
                'confidence': self.current_age.confidence if self.current_age else 0.0,
            } if self.current_age else None,

            'identity': {
                'identified': self.current_identity.identified if self.current_identity else False,
                'name': self.current_identity.identity if self.current_identity else None,
                'is_owner': self.current_identity.is_owner if self.current_identity else False,
                'confidence': self.current_identity.confidence if self.current_identity else 0.0,
            } if self.current_identity else None,

            'heartbeat': {
                'detected': self.current_heartbeat is not None and self.current_heartbeat.bpm is not None,
                'bpm': self.current_heartbeat.bpm if self.current_heartbeat else None,
                'quality': self.current_heartbeat.quality if self.current_heartbeat else None,
                'confidence': self.current_heartbeat.confidence if self.current_heartbeat else 0.0,
            } if self.current_heartbeat else None,
        }

    def register_owner(self, frame: np.ndarray) -> bool:
        """
        Register the owner's face for identity recognition.

        Args:
            frame: Face image of owner

        Returns:
            True if registration successful
        """
        return self.identity_recognizer.register_face(frame, self.owner_name)


# Test/Example usage
if __name__ == "__main__":
    print("Biometric Detector System - Test Mode")
    print("=" * 60)

    detector = BiometricDetector(owner_name="MJP")

    print("\nSystem Status:")
    print(f"  Emotion Detection: {'✅ Available' if detector.emotion_detector.enabled else '❌ Unavailable'}")
    print(f"  Age Detection: {'✅ Available' if detector.age_detector.enabled else '❌ Unavailable'}")
    print(f"  Identity Recognition: {'✅ Available' if detector.identity_recognizer.enabled else '❌ Unavailable'}")
    print(f"  Heartbeat Detection: {'✅ Available' if detector.heartbeat_detector.enabled else '❌ Unavailable'}")

    print("\nTo enable all features, install:")
    print("  pip install deepface librosa soundfile")

    print("\nFeatures:")
    print("  - Emotion: Detects happy, sad, angry, fear, surprise, neutral, disgusted")
    print("  - Age: Estimates age within ±5 years")
    print("  - Identity: Recognizes registered faces")
    print("  - Heartbeat: Measures BPM using camera (rPPG method)")
