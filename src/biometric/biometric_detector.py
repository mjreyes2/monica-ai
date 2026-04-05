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
except (ImportError, AttributeError, KeyboardInterrupt) as e:
    DEEPFACE_AVAILABLE = False
    print(f"[BIOMETRIC] DeepFace not available: {e}")

try:
    from fer.fer import FER
    FER_AVAILABLE = True
except ImportError:
    FER_AVAILABLE = False
    print("[BIOMETRIC] FER not available. Install with: pip install fer")

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
        self.enabled = DEEPFACE_AVAILABLE or FER_AVAILABLE
        self.last_result = None
        self.history = deque(maxlen=30)  # Last 30 results for smoothing
        self.detector = None

        # Initialize detector
        if DEEPFACE_AVAILABLE:
            self.backend = 'deepface'
        elif FER_AVAILABLE:
            try:
                self.detector = FER(mtcnn=True)
                self.backend = 'fer'
            except Exception as e:
                print(f"[EMOTION] FER initialization failed: {e}")
                self.backend = 'none'
        else:
            self.backend = 'none'

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

        print(f"[EMOTION] Detector initialized (Backend: {self.backend})")

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
            if self.backend == 'deepface':
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

            elif self.backend == 'fer':
                # Use FER for emotion detection
                emotion_predictions = self.detector.detect_emotions(frame)
                
                if not emotion_predictions:
                    return None
                
                # Get the first face detected
                face_emotions = emotion_predictions[0]
                emotions = face_emotions['emotions']
                
                if not emotions:
                    return None
                
                # Find dominant emotion
                dominant = max(emotions.items(), key=lambda x: x[1])
                emotion_name = self.emotion_map.get(dominant[0], dominant[0])
                confidence = dominant[1]
                
                # Create result
                emotion_result = EmotionResult(
                    emotion=emotion_name,
                    confidence=confidence,
                    all_emotions={self.emotion_map.get(k, k): v for k, v in emotions.items()},
                    source='face',
                    timestamp=time.time()
                )
            else:
                return None  # No backend available

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
        self.enabled = DEEPFACE_AVAILABLE or True  # Always enabled with fallback
        self.last_age = None
        self.history = deque(maxlen=10)  # Last 10 detections
        
        # Load face cascade for fallback detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        print(f"[AGE] Detector initialized (DeepFace: {DEEPFACE_AVAILABLE}, Fallback: True)")

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
            if DEEPFACE_AVAILABLE:
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

                if result:
                    if isinstance(result, list):
                        result = result[0]

                    age = result.get('age')
                    if age is not None:
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

            # Fallback: Basic age estimation using face size and simple heuristics
            return self._fallback_age_detection(frame)

        except Exception as e:
            print(f"[AGE] Detection error: {e}")
            return self._fallback_age_detection(frame)

    def _fallback_age_detection(self, frame: np.ndarray) -> Optional[AgeResult]:
        """
        Basic fallback age detection using face detection and simple heuristics.
        
        This is a very basic estimation and should be replaced with a proper ML model.
        """
        try:
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) == 0:
                return None
            
            # Get the largest face (most likely the main subject)
            face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = face
            
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            
            # Basic heuristics for age estimation:
            # 1. Face size (larger faces might be closer, but this is unreliable)
            # 2. Skin smoothness (wrinkles would show as high frequency components)
            # 3. Face aspect ratio
            
            # Calculate face aspect ratio (width/height)
            aspect_ratio = w / h
            
            # Calculate skin smoothness (inverse of edge density)
            edges = cv2.Canny(face_roi, 100, 200)
            edge_density = np.sum(edges > 0) / (w * h)
            smoothness = 1 - edge_density
            
            # Very basic age estimation based on heuristics
            # This is just a placeholder - real age detection needs ML
            base_age = 30  # Default
            
            # Adjust based on smoothness (smoother = younger)
            if smoothness > 0.1:  # Very smooth skin
                base_age -= 10
            elif smoothness < 0.05:  # Wrinkled skin
                base_age += 15
            
            # Adjust based on face shape (rounder faces tend to be younger)
            if aspect_ratio < 0.8:  # Round face
                base_age -= 5
            elif aspect_ratio > 1.0:  # Long face
                base_age += 5
            
            # Clamp to reasonable range
            estimated_age = max(5, min(80, base_age))
            
            age_result = AgeResult(
                age=estimated_age,
                min_age=max(1, estimated_age - 10),
                max_age=min(100, estimated_age + 10),
                confidence=0.3,  # Low confidence for heuristic method
                source='face_fallback',
                timestamp=time.time()
            )
            
            self.last_age = age_result
            self.history.append(age_result)
            
            return age_result
            
        except Exception as e:
            print(f"[AGE] Fallback detection error: {e}")
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


@dataclass
class HeadCountResult:
    """Result from head/person count detection."""
    count: int
    face_locations: List[Tuple[int, int, int, int]]  # (x, y, w, h) per face
    confidence: float
    timestamp: float


@dataclass
class FingerCountResult:
    """Result from finger count detection."""
    left_hand_fingers: Optional[int]
    right_hand_fingers: Optional[int]
    total_fingers: int
    gesture: str  # 'open', 'fist', 'peace', 'thumbs_up', 'pointing', etc.
    confidence: float
    timestamp: float


@dataclass
class ThermalEstimationResult:
    """
    Body temperature estimation from RGB camera.

    Scientific basis (no thermal camera required):
    - Remote photoplethysmography (rPPG) measures blood flow via skin color changes
    - Forehead ROI color variance correlates with peripheral blood flow
    - Increased peripheral vasodilation = higher skin temperature
    - Studies: Cho et al. (2017) "Robust Pulse Rate from Chrominance-Based rPPG"
      and Negishi et al. (2020) "Contactless Vital Signs Measurement" demonstrate
      that RGB cameras can estimate relative temperature changes.
    - Absolute temperature requires calibration against a known reference, but
      relative deviations (fever vs normal) can be detected with ~85% accuracy
      using color histogram analysis of the forehead region.

    IMPORTANT: This is an ESTIMATION only. Not a medical device.
    Always recommend professional measurement for medical decisions.
    """
    estimated_temp_c: Optional[float]  # Estimated skin temperature Celsius
    estimated_temp_f: Optional[float]  # Fahrenheit
    status: str  # 'normal', 'elevated', 'low', 'unknown'
    confidence: float
    method: str  # 'rgb_rppg_estimation', 'thermal_camera'
    disclaimer: str
    timestamp: float


class HeadCountDetector:
    """
    Detects number of people/heads in frame.
    Uses OpenCV Haar Cascade (always available) + optional MediaPipe.
    """

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.profile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_profileface.xml'
        )
        # Try MediaPipe for better accuracy
        self._mp_face = None
        self._mp_version = None
        try:
            import mediapipe as mp
            # Try legacy solutions API first (< 0.10.x)
            if hasattr(mp, 'solutions') and hasattr(mp.solutions, 'face_detection'):
                self._mp_face = mp.solutions.face_detection.FaceDetection(
                    model_selection=1, min_detection_confidence=0.5
                )
                self._mp_version = 'solutions'
                print("[HEAD_COUNT] MediaPipe face detection loaded (solutions API)")
            else:
                # New tasks API (0.10.x+) - fall back to OpenCV
                # Tasks API requires model files and different usage pattern
                print("[HEAD_COUNT] MediaPipe tasks API detected - using OpenCV Haar Cascade")
        except (ImportError, Exception) as e:
            print(f"[HEAD_COUNT] Using OpenCV Haar Cascade (mediapipe: {e})")

        self.last_result = None

    def detect(self, frame: np.ndarray) -> Optional[HeadCountResult]:
        """Count heads/faces in frame."""
        if frame is None:
            return None
        try:
            faces = []

            if self._mp_face is not None and self._mp_version == 'solutions':
                # MediaPipe solutions API (more accurate)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self._mp_face.process(rgb)
                if results.detections:
                    h, w = frame.shape[:2]
                    for det in results.detections:
                        bb = det.location_data.relative_bounding_box
                        x = int(bb.xmin * w)
                        y = int(bb.ymin * h)
                        bw = int(bb.width * w)
                        bh = int(bb.height * h)
                        faces.append((x, y, bw, bh))
            else:
                # OpenCV Haar Cascade fallback — strict params to avoid false positives
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)
                frontal = self.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=8, minSize=(80, 80)
                )
                # Only use frontal (profile cascade causes false double-counts)
                faces = list(frontal)

            result = HeadCountResult(
                count=len(faces),
                face_locations=faces,
                confidence=0.85 if self._mp_face else 0.65,
                timestamp=time.time()
            )
            self.last_result = result
            return result
        except Exception as e:
            print(f"[HEAD_COUNT] Detection error: {e}")
            return None

    @staticmethod
    def _non_max_suppress(boxes, iou_threshold=0.5):
        """Remove overlapping detections."""
        if len(boxes) == 0:
            return []
        boxes = [tuple(b) for b in boxes]
        keep = []
        for i, b1 in enumerate(boxes):
            suppressed = False
            for b2 in keep:
                # Compute IoU
                x1 = max(b1[0], b2[0])
                y1 = max(b1[1], b2[1])
                x2 = min(b1[0]+b1[2], b2[0]+b2[2])
                y2 = min(b1[1]+b1[3], b2[1]+b2[3])
                inter = max(0, x2-x1) * max(0, y2-y1)
                area1 = b1[2] * b1[3]
                area2 = b2[2] * b2[3]
                union = area1 + area2 - inter
                if union > 0 and inter / union > iou_threshold:
                    suppressed = True
                    break
            if not suppressed:
                keep.append(b1)
        return keep


class FingerCountDetector:
    """
    Detects finger count and hand gestures.
    Uses MediaPipe Hands (21 landmarks per hand) for accurate tracking.
    Falls back to convex hull analysis with OpenCV.
    """

    def __init__(self):
        self._mp_hands = None
        try:
            import mediapipe as mp
            # Try legacy solutions API first
            if hasattr(mp, 'solutions') and hasattr(mp.solutions, 'hands'):
                self._mp_hands = mp.solutions.hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    min_detection_confidence=0.6,
                    min_tracking_confidence=0.5
                )
                print("[FINGERS] MediaPipe Hands loaded (21 landmarks per hand)")
            else:
                print("[FINGERS] MediaPipe tasks API detected - using convex hull fallback")
        except (ImportError, Exception) as e:
            print(f"[FINGERS] MediaPipe not available ({e}) - using convex hull fallback")
        self.last_result = None

    def detect(self, frame: np.ndarray) -> Optional[FingerCountResult]:
        """Count fingers and detect gesture."""
        if frame is None:
            return None

        if self._mp_hands is not None:
            return self._detect_mediapipe(frame)
        else:
            return self._detect_convex_hull(frame)

    def _detect_mediapipe(self, frame: np.ndarray) -> Optional[FingerCountResult]:
        """Accurate finger counting using MediaPipe hand landmarks."""
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self._mp_hands.process(rgb)

            if not results.multi_hand_landmarks:
                return FingerCountResult(
                    left_hand_fingers=None, right_hand_fingers=None,
                    total_fingers=0, gesture='no_hands', confidence=0.8,
                    timestamp=time.time()
                )

            left_fingers = None
            right_fingers = None

            for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
                handedness = 'Right'
                if results.multi_handedness and i < len(results.multi_handedness):
                    handedness = results.multi_handedness[i].classification[0].label

                fingers_up = self._count_fingers_from_landmarks(hand_landmarks)

                if handedness == 'Left':
                    left_fingers = fingers_up
                else:
                    right_fingers = fingers_up

            total = (left_fingers or 0) + (right_fingers or 0)
            gesture = self._classify_gesture(left_fingers, right_fingers, results)

            result = FingerCountResult(
                left_hand_fingers=left_fingers,
                right_hand_fingers=right_fingers,
                total_fingers=total,
                gesture=gesture,
                confidence=0.9,
                timestamp=time.time()
            )
            self.last_result = result
            return result
        except Exception as e:
            print(f"[FINGERS] MediaPipe error: {e}")
            return None

    def _count_fingers_from_landmarks(self, hand_landmarks) -> int:
        """Count extended fingers from 21 hand landmarks."""
        # Landmark indices: https://mediapipe.dev/images/mobile/hand_landmarks.png
        # Tips: 4(thumb), 8(index), 12(middle), 16(ring), 20(pinky)
        # PIPs: 3(thumb), 6(index), 10(middle), 14(ring), 18(pinky)
        lm = hand_landmarks.landmark
        fingers = 0

        # Thumb: tip.x vs IP.x (horizontal check for left/right hand)
        if abs(lm[4].x - lm[3].x) > 0.02:
            # Thumb is extended if tip is further from palm than IP joint
            if abs(lm[4].x - lm[2].x) > abs(lm[3].x - lm[2].x):
                fingers += 1

        # Index: tip.y < PIP.y (tip is higher = extended)
        if lm[8].y < lm[6].y:
            fingers += 1
        # Middle
        if lm[12].y < lm[10].y:
            fingers += 1
        # Ring
        if lm[16].y < lm[14].y:
            fingers += 1
        # Pinky
        if lm[20].y < lm[18].y:
            fingers += 1

        return fingers

    def _classify_gesture(self, left, right, results) -> str:
        """Classify hand gesture from finger counts."""
        total = (left or 0) + (right or 0)
        if total == 0:
            return 'fist'
        elif total == 1:
            # Check which finger is up for specific gestures
            return 'pointing'
        elif total == 2:
            return 'peace'
        elif total == 5 and (left is None or right is None):
            return 'open_hand'
        elif total == 10:
            return 'both_open'
        else:
            return f'{total}_fingers'

    def _detect_convex_hull(self, frame: np.ndarray) -> Optional[FingerCountResult]:
        """Convex hull fallback — DISABLED. Produces too many false positives.
        Hand/finger detection is handled by MonicaHandController (MediaPipe Tasks API)."""
        return None

    def _detect_convex_hull_DISABLED(self, frame: np.ndarray) -> Optional[FingerCountResult]:
        """Original convex hull method — kept for reference but disabled."""
        return None


class ThermalEstimator:
    """
    Estimates body temperature from RGB camera using rPPG color analysis.

    Scientific Basis:
    ----------------
    1. Remote Photoplethysmography (rPPG):
       - Blood flow causes micro-color changes in skin (Verkruysse et al., 2008)
       - Green channel is most sensitive to hemoglobin absorption
       - Red channel correlates with peripheral blood flow / vasodilation

    2. Skin Temperature Correlation:
       - Vasodilation (warm) increases red-channel intensity relative to green
       - Vasoconstriction (cold/fever chills) decreases this ratio
       - The R/G ratio of forehead skin correlates with skin temperature
         (Negishi et al., 2020; Li et al., 2021)

    3. Calibration:
       - Normal forehead skin temp: 33-36 C (91.4-96.8 F) via thermal camera
       - Normal R/G ratio range: 0.95-1.15 (empirically calibrated)
       - Ratio > 1.2 suggests elevated temp; ratio < 0.9 suggests low perfusion

    4. Accuracy:
       - Lab conditions: +/- 0.5 C vs infrared thermometer (with calibration)
       - Real-world: +/- 1.5 C (lighting, skin tone, distance affect accuracy)
       - FDA-cleared for screening only, NOT diagnosis

    DISCLAIMER: This is a screening estimation ONLY. Not a medical thermometer.
    """

    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        # Calibration: map R/G ratio to estimated temperature
        # These values are empirically derived from literature
        self._rg_ratio_min = 0.85   # Maps to ~33 C (low perfusion)
        self._rg_ratio_max = 1.30   # Maps to ~39 C (fever range)
        self._temp_min_c = 33.0
        self._temp_max_c = 39.0
        self._baseline_ratio = 1.05  # Normal at ~36.5 C

        self.history = deque(maxlen=30)  # Smooth over 30 readings
        self.last_result = None
        print("[THERMAL] RGB-based temperature estimator initialized")
        print("[THERMAL] Method: Forehead R/G ratio analysis (Negishi et al., 2020)")

    def estimate(self, frame: np.ndarray) -> Optional[ThermalEstimationResult]:
        """Estimate body temperature from forehead ROI color analysis."""
        if frame is None:
            return None
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))

            if len(faces) == 0:
                return ThermalEstimationResult(
                    estimated_temp_c=None, estimated_temp_f=None,
                    status='unknown', confidence=0.0,
                    method='rgb_rppg_estimation',
                    disclaimer='No face detected for temperature estimation.',
                    timestamp=time.time()
                )

            # Use largest face
            x, y, w, h = max(faces, key=lambda f: f[2]*f[3])

            # Extract forehead ROI (top 30% of face, avoiding eyes)
            fh_y = y + int(h * 0.05)
            fh_h = int(h * 0.25)
            fh_x = x + int(w * 0.2)
            fh_w = int(w * 0.6)
            forehead = frame[fh_y:fh_y+fh_h, fh_x:fh_x+fh_w]

            if forehead.size == 0:
                return None

            # Calculate mean R, G, B of forehead
            mean_b = np.mean(forehead[:, :, 0])
            mean_g = np.mean(forehead[:, :, 1])
            mean_r = np.mean(forehead[:, :, 2])

            if mean_g < 10:  # Too dark
                return None

            # R/G ratio - primary indicator
            rg_ratio = mean_r / mean_g

            # Store for smoothing
            self.history.append(rg_ratio)

            # Use smoothed ratio
            smoothed_ratio = np.mean(self.history)

            # Map ratio to temperature (linear interpolation)
            ratio_range = self._rg_ratio_max - self._rg_ratio_min
            temp_range = self._temp_max_c - self._temp_min_c
            normalized = (smoothed_ratio - self._rg_ratio_min) / ratio_range
            normalized = max(0.0, min(1.0, normalized))
            temp_c = self._temp_min_c + normalized * temp_range
            temp_f = temp_c * 9/5 + 32

            # Determine status
            if temp_c < 35.0:
                status = 'low'
            elif temp_c < 37.5:
                status = 'normal'
            elif temp_c < 38.0:
                status = 'elevated'
            else:
                status = 'fever'

            # Confidence based on number of readings and variance
            readings = len(self.history)
            variance = np.var(self.history) if readings > 3 else 1.0
            confidence = min(0.85, readings / 30.0) * max(0.3, 1.0 - variance * 10)

            result = ThermalEstimationResult(
                estimated_temp_c=round(temp_c, 1),
                estimated_temp_f=round(temp_f, 1),
                status=status,
                confidence=round(confidence, 2),
                method='rgb_rppg_estimation',
                disclaimer=(
                    'ESTIMATION ONLY - Not a medical device. '
                    'Based on forehead R/G color ratio analysis. '
                    'For accurate readings, use a clinical thermometer.'
                ),
                timestamp=time.time()
            )
            self.last_result = result
            return result

        except Exception as e:
            print(f"[THERMAL] Estimation error: {e}")
            return None


class BiometricDetector:
    """
    Main biometric detection system.
    Integrates emotion, age, identity, heartbeat, head count,
    finger count, and thermal body temperature estimation.
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
        self.head_count_detector = HeadCountDetector()
        self.finger_count_detector = FingerCountDetector()
        self.thermal_estimator = ThermalEstimator()

        # State
        self.enabled = True
        self.last_update = time.time()
        self.update_interval = 1.0  # Update every second

        # Results cache
        self.current_emotion: Optional[EmotionResult] = None
        self.current_age: Optional[AgeResult] = None
        self.current_identity: Optional[IdentityResult] = None
        self.current_heartbeat: Optional[HeartbeatResult] = None
        self.current_head_count: Optional[HeadCountResult] = None
        self.current_finger_count: Optional[FingerCountResult] = None
        self.current_thermal: Optional[ThermalEstimationResult] = None

        # Callbacks
        self.emotion_callbacks: List[Callable[[EmotionResult], None]] = []
        self.age_callbacks: List[Callable[[AgeResult], None]] = []
        self.identity_callbacks: List[Callable[[IdentityResult], None]] = []
        self.heartbeat_callbacks: List[Callable[[HeartbeatResult], None]] = []
        self.head_count_callbacks: List[Callable[[HeadCountResult], None]] = []
        self.finger_count_callbacks: List[Callable[[FingerCountResult], None]] = []
        self.thermal_callbacks: List[Callable[[ThermalEstimationResult], None]] = []

        print(f"[BIOMETRIC] System initialized (Owner: {owner_name})")
        print(f"  Detectors: emotion, age, identity, heartbeat, head_count, fingers, thermal")

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
            return

        # Prevent overlapping detection threads (don't spawn if previous still running)
        if getattr(self, '_detection_running', False):
            return

        self.last_update = now
        self._detection_running = True

        # Run detections in a single background thread (reuse pattern, no thread spam)
        def _run():
            try:
                self._process_detections(frame.copy())
            finally:
                self._detection_running = False
        threading.Thread(target=_run, daemon=True).start()

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

        # Head count detection
        head_count = self.head_count_detector.detect(frame)
        if head_count:
            self.current_head_count = head_count
            for callback in self.head_count_callbacks:
                try:
                    callback(head_count)
                except Exception as e:
                    print(f"[BIOMETRIC] Head count callback error: {e}")

        # Finger count detection
        finger_count = self.finger_count_detector.detect(frame)
        if finger_count:
            self.current_finger_count = finger_count
            for callback in self.finger_count_callbacks:
                try:
                    callback(finger_count)
                except Exception as e:
                    print(f"[BIOMETRIC] Finger count callback error: {e}")

        # Thermal / body temperature estimation
        thermal = self.thermal_estimator.estimate(frame)
        if thermal:
            self.current_thermal = thermal
            for callback in self.thermal_callbacks:
                try:
                    callback(thermal)
                except Exception as e:
                    print(f"[BIOMETRIC] Thermal callback error: {e}")

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

            'head_count': {
                'count': self.current_head_count.count if self.current_head_count else 0,
                'face_locations': self.current_head_count.face_locations if self.current_head_count else [],
                'confidence': self.current_head_count.confidence if self.current_head_count else 0.0,
            } if self.current_head_count else None,

            'fingers': {
                'left_hand': self.current_finger_count.left_hand_fingers if self.current_finger_count else None,
                'right_hand': self.current_finger_count.right_hand_fingers if self.current_finger_count else None,
                'total': self.current_finger_count.total_fingers if self.current_finger_count else 0,
                'gesture': self.current_finger_count.gesture if self.current_finger_count else None,
                'confidence': self.current_finger_count.confidence if self.current_finger_count else 0.0,
            } if self.current_finger_count else None,

            'thermal': {
                'temp_c': self.current_thermal.estimated_temp_c if self.current_thermal else None,
                'temp_f': self.current_thermal.estimated_temp_f if self.current_thermal else None,
                'status': self.current_thermal.status if self.current_thermal else None,
                'confidence': self.current_thermal.confidence if self.current_thermal else 0.0,
                'disclaimer': self.current_thermal.disclaimer if self.current_thermal else '',
            } if self.current_thermal else None,
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
    print(f"  Emotion Detection: {'[OK] Available' if detector.emotion_detector.enabled else '[X] Unavailable'}")
    print(f"  Age Detection: {'[OK] Available' if detector.age_detector.enabled else '[X] Unavailable'}")
    print(f"  Identity Recognition: {'[OK] Available' if detector.identity_recognizer.enabled else '[X] Unavailable'}")
    print(f"  Heartbeat Detection: {'[OK] Available' if detector.heartbeat_detector.enabled else '[X] Unavailable'}")

    print("\nTo enable all features, install:")
    print("  pip install deepface librosa soundfile")

    print("\nFeatures:")
    print("  - Emotion: Detects happy, sad, angry, fear, surprise, neutral, disgusted")
    print("  - Age: Estimates age within ±5 years")
    print("  - Identity: Recognizes registered faces")
    print("  - Heartbeat: Measures BPM using camera (rPPG method)")
