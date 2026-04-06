"""
Monica's Integrated Vision System
Combines all computer vision capabilities:
- Hand detection and tracking
- Gesture recognition
- Emotion/Face detection
- Body pose estimation
- Object detection

Uses lazy loading for heavy modules (MediaPipe, TensorFlow, DeepFace) to ensure
fast startup while maintaining full functionality when features are accessed.
"""

import cv2
import numpy as np
import threading
import time
import sys
import os
from typing import Optional, Dict, List, Any, Tuple, Callable
from dataclasses import dataclass

# Add parent path for knowledge bases
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))

# =============================================================================
# LAZY LOADING SYSTEM
# Heavy modules are loaded on-demand, not at startup
# This dramatically improves startup time while keeping all features available
# =============================================================================

# Module availability flags - these will be updated when modules are actually loaded
HAS_MEDIAPIPE = None  # None = not checked yet, True/False = checked
HAS_GESTURE = None
HAS_HAND = None
HAS_EMOTION = None
HAS_AR_HOLOGRAM = None
HAS_VIDEO_ENHANCER = None
HAS_HAND_CONTROLLER = None
HAS_NIGHT_VISION = None
HAS_THERMAL_VISION = None
HAS_GESTURE_DETECTOR = None

# Cached module references
_mp = None  # MediaPipe
_mp_tasks = None
_mp_vision = None
_hand_detector_class = None
_gesture_detector_class = None
_emotion_intelligence_class = None
_ar_hologram_system = None
_video_enhancer = None
_hand_controller = None
_night_vision_class = None
_thermal_vision_class = None


def _load_mediapipe():
    """Lazy load MediaPipe."""
    global _mp, HAS_MEDIAPIPE
    if HAS_MEDIAPIPE is None:
        try:
            import mediapipe as mp
            _mp = mp
            HAS_MEDIAPIPE = True
            print("[OK] MediaPipe loaded for hand/pose detection")
        except ImportError:
            HAS_MEDIAPIPE = False
            print("[WARNING] MediaPipe not available")
    return _mp if HAS_MEDIAPIPE else None


def _load_mediapipe_tasks():
    """Lazy load MediaPipe gesture tasks."""
    global _mp_tasks, _mp_vision, HAS_GESTURE
    if HAS_GESTURE is None:
        mp = _load_mediapipe()
        if mp and hasattr(mp, 'tasks') and hasattr(mp.tasks, 'vision'):
            try:
                from mediapipe.tasks import python as mp_tasks  # type: ignore
                from mediapipe.tasks.python import vision as mp_vision  # type: ignore
                _mp_tasks = mp_tasks
                _mp_vision = mp_vision
                HAS_GESTURE = True
                print("[OK] MediaPipe gesture tasks available")
            except ImportError as e:
                HAS_GESTURE = False
                print(f"[WARNING] MediaPipe gesture tasks not available: {e}")
        else:
            HAS_GESTURE = False
    return (_mp_tasks, _mp_vision) if HAS_GESTURE else (None, None)


def _load_hand_detector():
    """Lazy load hand detector."""
    global _hand_detector_class, HAS_HAND
    if HAS_HAND is None:
        try:
            from vision.hand_detector import HandDetector
            _hand_detector_class = HandDetector
            HAS_HAND = True
            print("[OK] Hand detector loaded")
        except ImportError as e:
            HAS_HAND = False
            print(f"[WARNING] Hand detector not available: {e}")
    return _hand_detector_class if HAS_HAND else None


def _load_gesture_detector():
    """Lazy load gesture detector."""
    global _gesture_detector_class, HAS_GESTURE_DETECTOR
    if HAS_GESTURE_DETECTOR is None:
        try:
            from vision.gesture_detector import GestureDetector
            _gesture_detector_class = GestureDetector
            HAS_GESTURE_DETECTOR = True
            print("[OK] Gesture detector (finger counting) loaded")
        except ImportError:
            HAS_GESTURE_DETECTOR = False
    return _gesture_detector_class if HAS_GESTURE_DETECTOR else None


def _load_emotion_intelligence():
    """Lazy load emotion intelligence."""
    global _emotion_intelligence_class, HAS_EMOTION
    if HAS_EMOTION is None:
        try:
            from ai.monica_emotion_intelligence import MonicaEmotionIntelligence
            _emotion_intelligence_class = MonicaEmotionIntelligence
            HAS_EMOTION = True
            print("[OK] Emotion intelligence loaded")
        except ImportError as e:
            HAS_EMOTION = False
            print(f"[WARNING] Emotion intelligence not available: {e}")
    return _emotion_intelligence_class if HAS_EMOTION else None


def _load_ar_hologram():
    """Lazy load AR hologram system."""
    global _ar_hologram_system, HAS_AR_HOLOGRAM
    if HAS_AR_HOLOGRAM is None:
        try:
            from core.monica_ar_hologram_system import get_ar_hologram_system
            _ar_hologram_system = get_ar_hologram_system
            HAS_AR_HOLOGRAM = True
            print("[OK] AR Hologram System loaded")
        except ImportError as e:
            HAS_AR_HOLOGRAM = False
            print(f"[WARNING] AR Hologram System not available: {e}")
    return _ar_hologram_system if HAS_AR_HOLOGRAM else None


def _load_video_enhancer():
    """Lazy load video enhancer."""
    global _video_enhancer, HAS_VIDEO_ENHANCER
    if HAS_VIDEO_ENHANCER is None:
        try:
            from ui.monica_video_enhancer import get_video_enhancer
            _video_enhancer = get_video_enhancer
            HAS_VIDEO_ENHANCER = True
            print("[OK] Video Enhancer loaded (HDR-like quality)")
        except ImportError as e:
            HAS_VIDEO_ENHANCER = False
            print(f"[WARNING] Video Enhancer not available: {e}")
    return _video_enhancer if HAS_VIDEO_ENHANCER else None


def _load_hand_controller():
    """Lazy load hand controller."""
    global _hand_controller, HAS_HAND_CONTROLLER
    if HAS_HAND_CONTROLLER is None:
        try:
            from vision.monica_hand_controller import get_hand_controller
            _hand_controller = get_hand_controller
            HAS_HAND_CONTROLLER = True
            print("[OK] Hand Controller loaded (fingertip precision)")
        except ImportError as e:
            HAS_HAND_CONTROLLER = False
            print(f"[WARNING] Hand Controller not available: {e}")
    return _hand_controller if HAS_HAND_CONTROLLER else None


def _load_visual_capabilities():
    """Lazy load night vision and thermal vision."""
    global _night_vision_class, _thermal_vision_class, _terminator_vision_class, HAS_NIGHT_VISION, HAS_THERMAL_VISION
    if HAS_NIGHT_VISION is None:
        try:
            from vision.monica_visual_capabilities import NightVision, ThermalVision, TerminatorVision
            _night_vision_class = NightVision
            _thermal_vision_class = ThermalVision
            _terminator_vision_class = TerminatorVision
            HAS_NIGHT_VISION = True
            HAS_THERMAL_VISION = True
            print("[OK] Night Vision, Thermal Vision, and Terminator Vision loaded")
        except ImportError as e:
            import traceback
            traceback.print_exc()
            HAS_NIGHT_VISION = False
            HAS_THERMAL_VISION = False
            print(f"[WARNING] Advanced visual capabilities not available: {e}")
    return (_night_vision_class, _thermal_vision_class, _terminator_vision_class) if HAS_NIGHT_VISION else (None, None, None)

# Fallback classes - used if the real modules fail to load
class _FallbackNightVision:
    """Fallback night vision using simple OpenCV enhancement."""
    def __init__(self):
        self.enabled = False
    def apply(self, frame):
        if not self.enabled:
            return frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        result = np.zeros((frame.shape[0], frame.shape[1], 3), dtype=np.uint8)
        result[:, :, 1] = enhanced
        return result
    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled


class _FallbackThermalVision:
    """Fallback thermal vision using OpenCV colormap."""
    def __init__(self):
        self.enabled = False
    def apply(self, frame):
        if not self.enabled:
            return frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.applyColorMap(gray, cv2.COLORMAP_JET)
    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled


class _FallbackTerminatorVision:
    """Fallback terminator vision."""
    def __init__(self):
        self.enabled = False
    def apply(self, frame):
        if not self.enabled:
            return frame
        # Simple red tint
        result = frame.copy()
        result[:, :, 0] = 0
        result[:, :, 1] = 0
        return result
    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled


def get_night_vision_class():
    """Get NightVision class - real or fallback."""
    nv, _, _ = _load_visual_capabilities()
    return nv if nv else _FallbackNightVision


def get_thermal_vision_class():
    """Get ThermalVision class - real or fallback."""
    _, tv, _ = _load_visual_capabilities()
    return tv if tv else _FallbackThermalVision


def get_terminator_vision_class():
    """Get TerminatorVision class - real or fallback."""
    _, _, termv = _load_visual_capabilities()
    return termv if termv else _FallbackTerminatorVision

# Hologram System - lazy load
HAS_HOLOGRAM = None
_scifi_hologram_class = None

def _load_hologram():
    """Lazy load hologram system."""
    global _scifi_hologram_class, HAS_HOLOGRAM
    if HAS_HOLOGRAM is None:
        try:
            from vision.monica_hologram_scifi import SciFiHologram  # type: ignore
            _scifi_hologram_class = SciFiHologram
            HAS_HOLOGRAM = True
            print("[OK] Hologram System loaded")
        except ImportError:
            HAS_HOLOGRAM = False
    return _scifi_hologram_class if HAS_HOLOGRAM else None


@dataclass
class VisionResult:
    """Result from vision processing."""
    hands_detected: int = 0
    hand_landmarks: Optional[List[Any]] = None
    gestures: Optional[List[str]] = None
    finger_count: int = 0
    face_detected: bool = False
    face_location: Optional[Tuple[int, int, int, int]] = None  # x, y, w, h
    emotion: str = "neutral"
    emotion_confidence: float = 0.0
    body_pose: Any = None
    objects: Optional[List[Dict]] = None
    head_shake: bool = False  # User shaking head "no"
    head_nod: bool = False  # User nodding "yes"
    
    def __post_init__(self):
        if self.hand_landmarks is None:
            self.hand_landmarks = []
        if self.gestures is None:
            self.gestures = []
        if self.objects is None:
            self.objects = []


class MonicaVisionSystem:
    """
    Integrated vision system for Monica AI.
    Processes camera frames to detect hands, gestures, faces, emotions, and more.
    """
    
    def __init__(self):
        self.is_initialized = False
        self.is_running = False
        self.stop_event = threading.Event()
        
        # Detection modules - initialized lazily when first needed
        self.mp_hands = None
        self.mp_pose = None
        self.mp_face_mesh = None
        self.gesture_recognizer = None
        self.hand_detector = None
        self.gesture_detector = None
        self.emotion_intelligence = None
        self.ar_hologram = None  # AR Hologram System for in-feed overlays
        self.hologram = None
        
        # Biometric detector for identity, emotion, age, heartbeat
        self.biometric_detector = None
        self._biometric_data = {}  # Cache for biometric results
        
        # Vision effects - use fallback classes initially (lightweight)
        # Real classes will be loaded when features are used
        self.night_vision = get_night_vision_class()()
        self.thermal_vision = get_thermal_vision_class()()
        self.terminator_vision = get_terminator_vision_class()()
        
        # Face detection cascade (always available - lightweight)
        cascade_path = cv2.__file__.replace('__init__.py', '') + 'data/haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Results
        self.current_result = VisionResult()
        self.result_lock = threading.Lock()
        
        # Callbacks
        self.callbacks: List[Callable[[VisionResult], None]] = []
        
        # Head movement tracking for shake/nod detection
        self.head_positions = []  # Store recent head x positions
        self.head_y_positions = []  # Store recent head y positions
        self.max_head_history = 15  # Track last 15 frames
        
        # Processing settings - OPTIMIZED for performance
        # Process every 5th frame — at 15fps loop, this means ~3 detections/sec
        self.process_every_n_frames = 5  # Skip frames for better performance
        self.frame_count = 0
        
        # Stagger heavy operations to different frames
        self._emotion_frame_counter = 0
        self._pose_frame_counter = 0
        self._face_mesh_frame_counter = 0
        
        # Frame buffer for smoother processing - MINIMIZED for lower latency
        self._frame_buffer = []
        self._max_buffer_size = 1  # REDUCED from 2 to 1 to minimize lag
        
        # Detection overlay visibility - FORCE ENABLED to show all biometric data
        self.show_detection_overlays = True  # MUST be True to show hands, body, emotion, name

        self.identity_label = "MJP"
        
        # Lazy initialization flag
        self._heavy_modules_loaded = False
        
        # Temporal smoothing for hand tracking (reduces jitter while staying responsive)
        self._prev_hand_landmarks = None
        self._smoothing_factor = 0.2  # 0=no smoothing, 1=max smoothing. REDUCED from 0.5 to 0.2 for faster tracking

        # Persistence windows to reduce overlay flicker (face/hand boxes disappearing briefly)
        self._persist_sec = 1.5  # Increased from 0.5 to prevent overlay blinking
        self._last_face_time = 0.0
        self._last_face_bbox: Optional[Tuple[int, int, int, int]] = None
        self._last_hand_time = 0.0
        self._last_hand_landmarks_persist: List[Any] = []
        self._last_finger_count = 0
        
        # Basic initialization only - heavy modules loaded on first use
        print("[Vision] Monica Vision System ready (modules load on first use)")
    
    def _load_heavy_modules(self):
        """
        Lazy-load heavy vision modules on first use.
        This is called automatically when vision effects are first applied.
        OPTIMIZED: Loads modules progressively to avoid UI freeze.
        """
        if self._heavy_modules_loaded:
            return
        
        # Set flag IMMEDIATELY to prevent re-entry during loading
        self._heavy_modules_loaded = True
        
        print("\n[Vision] Loading modules in background (no freeze)...")
        
        # NOTE: mp.solutions.hands/pose/face_mesh removed in MediaPipe 0.10.20+
        # Hand detection is handled by MonicaHandController (Tasks API) in vision_service.
        # Do NOT initialize mp_hands/mp_pose/mp_face_mesh here — they will silently fail
        # and cause false finger counts via the gesture_detector fallback.
        self.mp_hands = None
        self.mp_pose = None
        self.mp_face_mesh = None
        self.hand_detector = None
        self.gesture_detector = None  # Disabled: produced false finger counts
        print("  [OK] Hand/pose detection delegated to HandController (Tasks API)")
        
        # Emotion intelligence
        EmotionClass = _load_emotion_intelligence()
        if EmotionClass:
            try:
                self.emotion_intelligence = EmotionClass()
                print("  [OK] Emotion intelligence initialized")
            except Exception as e:
                print(f"  [*] Emotion intelligence failed: {e}")
        
        # Biometric detector for identity, emotion, age, heartbeat
        try:
            from biometric import BiometricDetector
            self.biometric_detector = BiometricDetector(owner_name="MJP")
            print("  [OK] Biometric detector initialized")
        except Exception as e:
            print(f"  [*] Biometric detector failed: {e}")
            self.biometric_detector = None
        
        # AR Hologram System
        ar_hologram_getter = _load_ar_hologram()
        if ar_hologram_getter:
            try:
                self.ar_hologram = ar_hologram_getter()
                print("  [OK] AR Hologram System initialized")
            except Exception as e:
                print(f"  [*] AR Hologram System failed: {e}")
        
        # Video Enhancer DISABLED - using simple inline enhancement for speed
        self.video_enhancer = None
        
        # Hand Controller DISABLED - causes duplicate detection and lag
        self.hand_controller = None
        
        self._heavy_modules_loaded = True
        self.is_initialized = True
        print("[Search] Vision modules loaded successfully")
    
    def _initialize(self):
        """Legacy initialize method - now just calls lazy loader."""
        self._load_heavy_modules()
        
        # Hologram System - lazy load
        HologramClass = _load_hologram()
        if HologramClass:
            try:
                self.hologram = HologramClass()
                print("  [OK] Hologram System initialized")
            except Exception as e:
                print(f"  [*] Hologram System failed: {e}")
        
        self.is_initialized = True
        print("[OK] Monica Vision System ready!\n")
    
    def _detect_head_shake(self, face_x: int) -> bool:
        """
        Head shake detection DISABLED - was causing too many false positives.
        """
        return False
    
    def _detect_head_nod(self, face_y: int) -> bool:
        """
        Head nod detection DISABLED - was causing too many false positives.
        """
        return False
    
    def _count_fingers_from_landmarks(self, hand_landmarks, handedness: str = "Right") -> int:
        """
        Count raised fingers from MediaPipe hand landmarks.
        IMPROVED algorithm with better accuracy for all hand orientations.
        
        Args:
            hand_landmarks: MediaPipe hand landmarks
            handedness: "Left" or "Right" hand
            
        Returns:
            Number of fingers raised (0-5)
        """
        try:
            landmarks = hand_landmarks.landmark
            fingers_up = 0
            
            # Get key reference points
            wrist = landmarks[0]
            index_mcp = landmarks[5]
            middle_mcp = landmarks[9]
            pinky_mcp = landmarks[17]
            
            # Determine hand orientation (palm facing camera or away)
            palm_facing = (pinky_mcp.x < index_mcp.x) if handedness == "Right" else (pinky_mcp.x > index_mcp.x)
            
            # ===== THUMB DETECTION =====
            thumb_tip = landmarks[4]
            thumb_ip = landmarks[3]
            thumb_mcp = landmarks[2]
            thumb_cmc = landmarks[1]
            
            # Calculate thumb extension based on distance from palm center
            palm_center_x = (index_mcp.x + pinky_mcp.x) / 2
            thumb_dist_from_palm = abs(thumb_tip.x - palm_center_x)
            thumb_ip_dist = abs(thumb_ip.x - palm_center_x)
            
            # Thumb is up if tip is further from palm than IP joint (reduced threshold)
            thumb_up = thumb_dist_from_palm > thumb_ip_dist + 0.02
            
            if thumb_up:
                fingers_up += 1
            
            # ===== OTHER FINGERS DETECTION =====
            # SIMPLIFIED: Finger is up if tip.y < pip.y (tip above PIP in image coords)
            finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky tips
            finger_pips = [6, 10, 14, 18]  # PIP joints
            finger_mcps = [5, 9, 13, 17]   # MCP joints
            
            for i in range(4):
                tip = landmarks[finger_tips[i]]
                pip = landmarks[finger_pips[i]]
                mcp = landmarks[finger_mcps[i]]
                
                # Simple check: tip is above PIP (lower y value in image coords)
                # Reduced threshold for better sensitivity
                if tip.y < pip.y - 0.015:
                    fingers_up += 1
            
            return fingers_up
            
        except Exception as e:
            print(f"[VISION] Finger count error: {e}")
            return 0
    
    def _apply_temporal_smoothing(self, current_landmarks):
        """
        Apply exponential moving average (EMA) smoothing to hand landmarks.
        This reduces jitter and makes tracking stable and locked onto detected parts.
        
        Args:
            current_landmarks: Current frame's hand landmarks from MediaPipe
            
        Returns:
            Smoothed hand landmarks
        """
        if self._prev_hand_landmarks is None or len(self._prev_hand_landmarks) != len(current_landmarks):
            # First frame or hand count changed - no smoothing
            self._prev_hand_landmarks = current_landmarks
            return current_landmarks
        
        try:
            smoothed = []
            for curr_hand, prev_hand in zip(current_landmarks, self._prev_hand_landmarks):
                # Create a new hand landmark object with smoothed values
                import copy
                smoothed_hand = copy.deepcopy(curr_hand)
                
                # Apply EMA to each landmark point
                for i, (curr_lm, prev_lm) in enumerate(zip(curr_hand.landmark, prev_hand.landmark)):
                    # Smooth x, y, z coordinates
                    smoothed_hand.landmark[i].x = (
                        self._smoothing_factor * prev_lm.x + 
                        (1 - self._smoothing_factor) * curr_lm.x
                    )
                    smoothed_hand.landmark[i].y = (
                        self._smoothing_factor * prev_lm.y + 
                        (1 - self._smoothing_factor) * curr_lm.y
                    )
                    smoothed_hand.landmark[i].z = (
                        self._smoothing_factor * prev_lm.z + 
                        (1 - self._smoothing_factor) * curr_lm.z
                    )
                
                smoothed.append(smoothed_hand)
            
            # Store for next frame
            self._prev_hand_landmarks = smoothed
            return smoothed
            
        except Exception as e:
            print(f"[VISION] Smoothing error: {e}")
            self._prev_hand_landmarks = current_landmarks
            return current_landmarks
    
    def process_frame(self, frame: np.ndarray) -> VisionResult:
        """
        Process a camera frame through all vision modules.
        
        Args:
            frame: BGR image from camera
            
        Returns:
            VisionResult with all detections
        """
        if frame is None:
            return VisionResult()
        
        # Lazy load heavy modules on first frame processing
        if not self._heavy_modules_loaded:
            self._load_heavy_modules()
        
        self.frame_count += 1
        
        # Skip some frames for performance
        if self.frame_count % self.process_every_n_frames != 0:
            with self.result_lock:
                return self.current_result
        
        result = VisionResult()
        
        # Convert to RGB only if needed by active MediaPipe modules
        rgb_frame = None
        if self.mp_hands or self.mp_pose:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 1. Hand Detection (MediaPipe) with finger counting
        if self.mp_hands:
            try:
                hands_result = self.mp_hands.process(rgb_frame)
                if hands_result.multi_hand_landmarks:
                    result.hands_detected = len(hands_result.multi_hand_landmarks)
                    
                    # Apply temporal smoothing to reduce jitter
                    smoothed_landmarks = self._apply_temporal_smoothing(hands_result.multi_hand_landmarks)
                    result.hand_landmarks = smoothed_landmarks
                    
                    # Count fingers using smoothed landmarks with handedness info
                    total_fingers = 0
                    for idx, hand_landmarks in enumerate(smoothed_landmarks):
                        # Get handedness (Left/Right)
                        handedness = "Right"
                        if idx < len(hands_result.multi_handedness):
                            handedness = hands_result.multi_handedness[idx].classification[0].label
                        
                        fingers = self._count_fingers_from_landmarks(hand_landmarks, handedness)
                        total_fingers += fingers
                    result.finger_count = total_fingers
                else:
                    # Reset smoothing when no hands detected
                    self._prev_hand_landmarks = None
            except Exception as e:
                pass
        
        # 2. Gesture Recognition (only if hands were detected)
        if result.hands_detected > 0 and result.hand_data:
            try:
                gestures = []
                for hand in result.hand_data:
                    if hasattr(hand, 'get_gesture'):
                        gesture = hand.get_gesture()
                        if gesture and gesture != "unknown":
                            gestures.append(gesture)
                    elif self.hand_detector:
                        # Fallback to hand_detector's gesture recognition
                        gesture = self.hand_detector.get_gesture(hand)
                        if gesture and gesture != "unknown":
                            gestures.append(gesture)
                if gestures:
                    result.gestures = gestures
            except Exception as e:
                pass
        
        # 3. Finger Counting (fallback) — DISABLED: produced false positives
        # Hand detection is now handled by MonicaHandController in vision_service

        # Hand persistence to avoid flicker between frames
        now_ts = time.time()
        if result.hands_detected > 0 and result.hand_landmarks:
            self._last_hand_time = now_ts
            self._last_hand_landmarks_persist = result.hand_landmarks
            if getattr(result, 'finger_count', 0) > 0:
                self._last_finger_count = result.finger_count
        else:
            if (now_ts - self._last_hand_time) <= self._persist_sec and self._last_hand_landmarks_persist:
                result.hands_detected = len(self._last_hand_landmarks_persist)
                result.hand_landmarks = self._last_hand_landmarks_persist
                if getattr(result, 'finger_count', 0) == 0 and self._last_finger_count > 0:
                    result.finger_count = self._last_finger_count
        
        # 4. Face Detection + Head Shake/Nod Detection
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=8, minSize=(80, 80)
            )
            if len(faces) > 0:
                result.face_detected = True
                x, y, w, h = faces[0]
                result.face_location = (x, y, w, h)
                # Update persistence state
                self._last_face_time = time.time()
                self._last_face_bbox = (x, y, w, h)
                
                # Detect head shake (no) and nod (yes)
                face_center_x = x + w // 2
                face_center_y = y + h // 2
                result.head_shake = self._detect_head_shake(face_center_x)
                result.head_nod = self._detect_head_nod(face_center_y)
            else:
                # Apply face persistence if recent
                if (time.time() - self._last_face_time) <= self._persist_sec and self._last_face_bbox is not None:
                    result.face_detected = True
                    result.face_location = self._last_face_bbox
        except Exception as e:
            pass
        
        # 5. Emotion Detection - STAGGERED (every 6th processed frame = ~18 real frames)
        self._emotion_frame_counter += 1
        if self.emotion_intelligence and result.face_detected and self._emotion_frame_counter >= 6:
            self._emotion_frame_counter = 0
            try:
                emotion_result = self.emotion_intelligence.detect_emotion_from_face(frame)
                if emotion_result:
                    result.emotion = emotion_result.get('emotion', 'neutral')
                    result.emotion_confidence = emotion_result.get('confidence', 0.0)
            except Exception as e:
                pass
        
        # 6. Body Pose - STAGGERED (every 4th processed frame = ~12 real frames)
        self._pose_frame_counter += 1
        if self.mp_pose and self._pose_frame_counter >= 4:
            self._pose_frame_counter = 0
            try:
                pose_result = self.mp_pose.process(rgb_frame)
                if pose_result.pose_landmarks:
                    result.body_pose = pose_result.pose_landmarks
            except Exception as e:
                pass
        
        # 7. Biometric Detection — DELEGATED to vision_service (has its own instance)
        # Removed duplicate processing here to reduce lag
        
        # Store result
        with self.result_lock:
            self.current_result = result
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(result)
            except Exception:
                pass
        
        return result
    
    def get_current_result(self) -> VisionResult:
        """Get the most recent vision result."""
        with self.result_lock:
            return self.current_result
    
    def add_callback(self, callback: Callable[[VisionResult], None]):
        """Add a callback for vision results."""
        self.callbacks.append(callback)
    
    def draw_detections(self, frame: np.ndarray, result: Optional[VisionResult] = None) -> np.ndarray:
        """
        Draw detection overlays on frame.
        
        PERFORMANCE OPTIMIZATION: Detection overlays are DISABLED by default
        to reduce video lag. Detection still runs in background.
        Set self.show_detection_overlays = True to enable.
        
        Args:
            frame: BGR image
            result: VisionResult to visualize (uses current if None)
            
        Returns:
            Frame with overlays drawn (or original frame if disabled)
        """
        # PERFORMANCE: Skip drawing overlays to reduce lag
        # Detection still runs, just not visualized
        # CHANGED: Default to True so user can see Identity/Emotion overlays
        if not getattr(self, 'show_detection_overlays', True):
            return frame
        
        if result is None:
            result = self.get_current_result()
        
        output = frame.copy()
        h, w = output.shape[:2]
        
        # Draw hand landmarks
        mp = _load_mediapipe()  # Get lazy-loaded mediapipe
        if mp and result.hand_landmarks:
            mp_drawing = mp.solutions.drawing_utils
            mp_hands_style = mp.solutions.hands
            for hand_landmarks in result.hand_landmarks:
                mp_drawing.draw_landmarks(
                    output, hand_landmarks, mp_hands_style.HAND_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                    mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2)
                )
        
        # Draw FaceMesh - DISABLED for performance (very heavy operation)
        # Uncomment below if you need face mesh visualization
        # if mp and hasattr(self, 'mp_face_mesh') and self.mp_face_mesh:
        #     try:
        #         rgb_frame = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
        #         face_results = self.mp_face_mesh.process(rgb_frame)
        #         if face_results.multi_face_landmarks:
        #             mp_drawing = mp.solutions.drawing_utils
        #             mp_face_mesh_style = mp.solutions.face_mesh
        #             for face_landmarks in face_results.multi_face_landmarks:
        #                 mp_drawing.draw_landmarks(
        #                     output, face_landmarks, mp_face_mesh_style.FACEMESH_CONTOURS,
        #                     landmark_drawing_spec=None,
        #                     connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1)
        #                 )
        #     except Exception as e:
        #         pass

        if mp and hasattr(self, 'mp_face_mesh') and self.mp_face_mesh:
            try:
                rgb_frame = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)
                face_results = self.mp_face_mesh.process(rgb_frame)
                if face_results.multi_face_landmarks:
                    mp_drawing = mp.solutions.drawing_utils
                    mp_face_mesh_style = mp.solutions.face_mesh
                    for face_landmarks in face_results.multi_face_landmarks:
                        mp_drawing.draw_landmarks(
                            output,
                            face_landmarks,
                            mp_face_mesh_style.FACEMESH_TESSELATION,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=1)
                        )
                        mp_drawing.draw_landmarks(
                            output,
                            face_landmarks,
                            mp_face_mesh_style.FACEMESH_CONTOURS,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1)
                        )
                        mp_drawing.draw_landmarks(
                            output,
                            face_landmarks,
                            mp_face_mesh_style.FACEMESH_IRISES,
                            landmark_drawing_spec=None,
                            connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=1)
                        )
            except Exception as e:
                if not hasattr(self, '_face_mesh_draw_error_logged'):
                    print(f"  [*] MediaPipe FaceMesh draw failed: {e}")
                    self._face_mesh_draw_error_logged = True
        
        # Draw face bounding box + identity (if face detected)
        if result.face_detected and result.face_location:
            x, y, fw, fh = result.face_location
            try:
                # Face box for better anchoring
                cv2.rectangle(output, (x, y), (x + fw, y + fh), (0, 255, 0), 2)
            except Exception:
                pass
            if self.identity_label:
                cv2.putText(output, f"Identity: {self.identity_label}", (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Draw full body pose with joint labels (arms, shoulders, torso, hips, legs)
        if mp and result.body_pose:
            try:
                mp_drawing = mp.solutions.drawing_utils
                mp_pose_style = mp.solutions.pose
                # Draw pose landmarks with custom style
                mp_drawing.draw_landmarks(
                    output, result.body_pose, mp_pose_style.POSE_CONNECTIONS,
                    landmark_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                    connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=2)
                )
                
                # Label key body parts
                landmarks = result.body_pose.landmark
                pose_labels = {
                    11: 'L Shoulder', 12: 'R Shoulder',
                    13: 'L Elbow', 14: 'R Elbow',
                    15: 'L Wrist', 16: 'R Wrist',
                    23: 'L Hip', 24: 'R Hip',
                    25: 'L Knee', 26: 'R Knee',
                    27: 'L Ankle', 28: 'R Ankle'
                }
                for idx, label in pose_labels.items():
                    if idx < len(landmarks):
                        lm = landmarks[idx]
                        if lm.visibility > 0.5:  # Only show if visible
                            px, py = int(lm.x * w), int(lm.y * h)
                            cv2.putText(output, label, (px + 5, py - 5),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 0), 1)
            except Exception:
                pass
        
        # Draw gesture info
        if result.gestures:
            y_pos = 30
            for gesture in result.gestures:
                cv2.putText(output, f"Gesture: {gesture}", (10, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                y_pos += 30
        
        # Draw finger count
        if result.finger_count > 0:
            cv2.putText(output, f"Fingers: {result.finger_count}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Draw hands detected
        cv2.putText(output, f"Hands: {result.hands_detected}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Draw biometric data panel (top-right corner) - LARGER SIZE for better visibility
        panel_x = w - 450  # Increased from 280 to 450
        panel_y = 10
        panel_w = 440  # Increased from 270 to 440
        panel_h = 260  # Increased from 200 to 260

        # Semi-transparent background
        overlay = output.copy()
        cv2.rectangle(overlay, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h),
                     (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, output, 0.4, 0, output)
        cv2.rectangle(output, (panel_x, panel_y), (panel_x + panel_w, panel_y + panel_h),
                     (0, 255, 255), 2)

        # Title - LARGER font
        cv2.putText(output, "BIOMETRIC DATA", (panel_x + 15, panel_y + 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)  # Increased from 0.6 to 0.9

        # Get biometric data
        y_offset = panel_y + 70  # Increased spacing from 50 to 70
        line_height = 38  # Increased from 25 to 38 for better readability

        biometric_data = {}
        # 1) Prefer locally computed vision results (always available in this GUI)
        try:
            if result:
                if result.face_detected:
                    # Show owner identity when a face is present (updated when recognizer is integrated)
                    biometric_data['identity'] = self.identity_label or "Unknown"
                if getattr(result, 'emotion', None):
                    conf = getattr(result, 'emotion_confidence', 0.0)
                    if result.emotion and (result.emotion != 'neutral' or conf > 0.0):
                        biometric_data['emotion'] = f"{str(result.emotion).title()}" + (f" ({conf*100:.0f}%)" if conf and conf > 0 else "")
        except Exception:
            pass

        # 2) Use local biometric detector if available
        try:
            bio = self.biometric_detector
            if bio:
                if bio.current_emotion and 'emotion' not in biometric_data:
                    biometric_data['emotion'] = f"{bio.current_emotion.emotion.title()} ({bio.current_emotion.confidence*100:.0f}%)"
                if bio.current_age:
                    biometric_data['age'] = f"{bio.current_age.age} years"
                if bio.current_heartbeat and getattr(bio.current_heartbeat, 'bpm', None):
                    biometric_data['heart_rate'] = f"{bio.current_heartbeat.bpm:.0f} BPM ({bio.current_heartbeat.quality})"
                if bio.current_identity and 'identity' not in biometric_data:
                    biometric_data['identity'] = bio.current_identity.identity if bio.current_identity.identified else "Unknown"
        except Exception:
            pass
        
        # 3) Fallback to _sys._monica_app.biometric if local detector not available
        if not biometric_data.get('identity') and not biometric_data.get('emotion'):
            try:
                import sys as _sys
                if hasattr(_sys, '_monica_app') and hasattr(_sys._monica_app, 'biometric'): # type: ignore
                    bio = _sys._monica_app.biometric # type: ignore
                    if bio:
                        if bio.current_emotion and 'emotion' not in biometric_data:
                            biometric_data['emotion'] = f"{bio.current_emotion.emotion.title()} ({bio.current_emotion.confidence*100:.0f}%)"
                        if bio.current_age:
                            biometric_data['age'] = f"{bio.current_age.age} years"
                        if bio.current_heartbeat and getattr(bio.current_heartbeat, 'bpm', None):
                            biometric_data['heart_rate'] = f"{bio.current_heartbeat.bpm:.0f} BPM ({bio.current_heartbeat.quality})"
                        if bio.current_identity and 'identity' not in biometric_data:
                            biometric_data['identity'] = bio.current_identity.identity if bio.current_identity.identified else "Unknown"
            except Exception:
                pass
        
        # Display biometric data - LARGER fonts for better visibility
        cv2.putText(output, f"Identity: {biometric_data.get('identity', 'Detecting...')}",
                   (panel_x + 15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)  # Increased from 0.5 to 0.7, thickness 1 to 2
        y_offset += line_height

        cv2.putText(output, f"Emotion: {biometric_data.get('emotion', 'Detecting...')}",
                   (panel_x + 15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)  # Increased from 0.5 to 0.7, thickness 1 to 2
        y_offset += line_height

        cv2.putText(output, f"Age: {biometric_data.get('age', 'Detecting...')}",
                   (panel_x + 15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)  # Increased from 0.5 to 0.7, thickness 1 to 2
        y_offset += line_height

        cv2.putText(output, f"Heart Rate: {biometric_data.get('heart_rate', 'Detecting...')}",
                   (panel_x + 15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)  # Increased from 0.5 to 0.7, thickness 1 to 2
        y_offset += line_height

        # Temperature (placeholder - requires thermal camera or estimation)
        cv2.putText(output, "Temperature: Estimating...",
                   (panel_x + 15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)  # Increased from 0.5 to 0.7, thickness 1 to 2
        y_offset += line_height

        # Connection status
        connection_color = (0, 255, 0) if biometric_data else (255, 0, 0)
        status_text = "Connected" if biometric_data else "Initializing"
        cv2.putText(output, f"Status: {status_text}",
                   (panel_x + 15, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.7, connection_color, 2)  # Increased from 0.5 to 0.7, thickness 1 to 2
        
        return output
    
    def toggle_detection_overlays(self, show: Optional[bool] = None) -> bool:
        """Toggle visibility of detection overlays (hands, face boxes, etc.)."""
        if show is None:
            self.show_detection_overlays = not getattr(self, 'show_detection_overlays', False)
        else:
            self.show_detection_overlays = show
        return self.show_detection_overlays
    
    def get_status_text(self) -> str:
        """Get a text description of current vision state."""
        result = self.get_current_result()
        
        parts = []
        
        if result.face_detected:
            parts.append("Face detected")
        
        if result.hands_detected > 0:
            parts.append(f"{result.hands_detected} hand(s)")
            if result.gestures:
                parts.append(f"Gestures: {', '.join(result.gestures)}")
            if result.finger_count > 0:
                parts.append(f"{result.finger_count} fingers")
        
        if result.body_pose:
            parts.append("Body pose detected")
        
        return " | ".join(parts) if parts else "No detections"
    
    def toggle_night_vision(self) -> bool:
        """Toggle night vision mode on/off."""
        if self.night_vision:
            enabled = self.night_vision.toggle()
            print(f"[VISION] Night vision: {'ON' if enabled else 'OFF'}")
            return enabled
        return False
    
    def toggle_thermal_vision(self) -> bool:
        """Toggle thermal/heat vision mode on/off."""
        if self.thermal_vision:
            enabled = self.thermal_vision.toggle()
            print(f"[VISION] Thermal vision: {'ON' if enabled else 'OFF'}")
            return enabled
        return False
    
    def toggle_terminator_vision(self) -> bool:
        """Toggle terminator vision mode on/off (red HUD overlay)."""
        if self.terminator_vision:
            enabled = self.terminator_vision.toggle()
            print(f"[VISION] Terminator vision: {'ON' if enabled else 'OFF'}")
            return enabled
        return False
    
    def apply_vision_effects(self, frame: np.ndarray) -> np.ndarray:
        """Apply any active vision effects (night vision, thermal, AR holograms, video enhancement, etc.)."""
        if frame is None:
            return frame
        
        # Apply video enhancement FIRST for better quality (FAST mode)
        # Simple fast video enhancement (inline - no external module)
        # Just basic contrast/brightness for better quality without lag
        try:
            frame = cv2.convertScaleAbs(frame, alpha=1.1, beta=10)
        except:
            pass
        
        # NOTE: Hand detection is already done in process_frame()
        # Don't run hand_controller.process_frame() here - it duplicates detection and causes lag
        
        # Apply night vision if enabled
        if self.night_vision and self.night_vision.enabled:
            frame = self.night_vision.apply(frame)
        
        # Apply thermal vision if enabled
        if self.thermal_vision and self.thermal_vision.enabled:
            frame = self.thermal_vision.apply(frame)
        
        # Apply terminator vision if enabled (red HUD overlay)
        if self.terminator_vision and self.terminator_vision.enabled:
            frame = self.terminator_vision.apply(frame)
        
        # Draw detection overlays (hands, face, gestures)
        frame = self.draw_detections(frame)
        
        # Apply AR hologram overlays (globe, webcam windows, etc.)
        if self.ar_hologram:
            # Pass hand landmarks for gesture control (use existing detection)
            if hasattr(self, 'current_result') and self.current_result:
                h, w = frame.shape[:2]
                try:
                    if hasattr(self.current_result, 'face_location') and self.current_result.face_location:
                        if hasattr(self.ar_hologram, 'last_face_location'):
                            setattr(self.ar_hologram, 'last_face_location', self.current_result.face_location)
                except Exception:
                    pass
                # Get hand landmarks from current detection result
                if hasattr(self.current_result, 'hand_landmarks') and self.current_result.hand_landmarks:
                    self.ar_hologram.process_hand_gesture(
                        self.current_result.hand_landmarks,
                        w, h
                    )
                    # Get index fingertip from landmarks for keyboard/button interaction
                    try:
                        hand_lm = self.current_result.hand_landmarks[0]
                        index_tip = hand_lm.landmark[8]  # Index fingertip
                        fx, fy = int(index_tip.x * w), int(index_tip.y * h)
                        
                        # Check button press
                        action = self.ar_hologram.check_button_press(fx, fy)
                        if action:
                            self.ar_hologram.handle_control_button(action)
                        
                        # Check keyboard press
                        key = self.ar_hologram.check_keyboard_press(fx, fy, h, w)
                    except:
                        pass
                else:
                    # No hand detected - let AR system handle momentum
                    self.ar_hologram.process_hand_gesture([], w, h)
            
            # Render AR overlay (frame is already BGR from camera)
            frame = self.ar_hologram.render_overlay(frame)
        
        return frame
    
    def process_ar_command(self, text: str) -> Optional[str]:
        """
        Process voice/text commands for AR holograms.
        
        Args:
            text: User's voice command or text input
            
        Returns:
            Response text if command was handled, None otherwise
        """
        if self.ar_hologram:
            return self.ar_hologram.process_command(text)
        return None
    
    def show_globe(self) -> str:
        """Show the holographic globe in the camera feed."""
        if self.ar_hologram:
            return self.ar_hologram.show_globe()
        return "AR hologram system not available."
    
    def hide_globe(self) -> str:
        """Hide the holographic globe."""
        if self.ar_hologram:
            return self.ar_hologram.hide_globe()
        return "AR hologram system not available."
    
    def highlight_location(self, location: str) -> str:
        """Highlight a location on the globe."""
        if self.ar_hologram:
            return self.ar_hologram.highlight_location(location)
        return "AR hologram system not available."
    
    def zoom_globe(self, direction: str) -> str:
        """Zoom the globe in or out."""
        if self.ar_hologram:
            if "in" in direction.lower():
                return self.ar_hologram.zoom_in()
            else:
                return self.ar_hologram.zoom_out()
        return "AR hologram system not available."
    
    def show_webcam_feed(self, feeds: Optional[List[Dict]] = None) -> str:
        """Show webcam feed window, replacing the globe."""
        if self.ar_hologram:
            return self.ar_hologram.show_webcam_feed(feeds=feeds or [])
        return "AR hologram system not available."
    
    def return_to_globe(self) -> str:
        """Return to globe view from webcam window."""
        if self.ar_hologram:
            return self.ar_hologram.return_to_globe()
        return "AR hologram system not available."
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_event.set()
        
        if self.mp_hands:
            self.mp_hands.close()
        if self.mp_pose:
            self.mp_pose.close()
        
        print("Vision system cleaned up")


# Singleton instance
_vision_system = None

def get_vision_system() -> MonicaVisionSystem:
    """Get the singleton vision system instance."""
    global _vision_system
    if _vision_system is None:
        _vision_system = MonicaVisionSystem()
    return _vision_system

