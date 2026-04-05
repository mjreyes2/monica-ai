"""
Monica Hand Controller - Improved Hand & Fingertip Detection
Provides precise fingertip tracking for keyboard and dial interaction.
Includes gesture recognition for dial rotation and alarm triggers.
"""
import cv2
import numpy as np
import math
import time
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Try to import MediaPipe Tasks API (0.10.20+)
HAS_MEDIAPIPE = False
_HandLandmarker = None
_HandLandmarkerOptions = None
_BaseOptions = None
_VisionRunningMode = None
try:
    import mediapipe as mp
    from mediapipe.tasks.python.vision import HandLandmarker as _HandLandmarker
    from mediapipe.tasks.python.vision import HandLandmarkerOptions as _HandLandmarkerOptions
    from mediapipe.tasks.python.vision import RunningMode as _VisionRunningMode
    from mediapipe.tasks.python import BaseOptions as _BaseOptions
    HAS_MEDIAPIPE = True
except (ImportError, AttributeError):
    try:
        # Fallback: legacy mp.solutions API (mediapipe < 0.10.20)
        import mediapipe as mp
        if hasattr(mp, 'solutions'):
            HAS_MEDIAPIPE = True
    except ImportError:
        pass

if not HAS_MEDIAPIPE:
    print("[WARN] MediaPipe not available for hand detection")

# Hand skeleton connections (21 landmarks)
HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),       # Thumb
    (0,5),(5,6),(6,7),(7,8),       # Index
    (5,9),(9,10),(10,11),(11,12),  # Middle
    (9,13),(13,14),(14,15),(15,16),# Ring
    (13,17),(17,18),(18,19),(19,20),# Pinky
    (0,17),                         # Palm base
]


class _LandmarkListWrapper:
    """Wrapper to make Tasks API landmarks compatible with legacy .landmark[idx] access."""
    def __init__(self, landmark_list):
        self.landmark = landmark_list  # list of NormalizedLandmark with .x, .y, .z


class GestureType(Enum):
    NONE = "none"
    POINT = "point"           # Index finger pointing
    FIST = "fist"             # Closed fist
    OPEN_PALM = "open_palm"   # All fingers extended
    ROTATE_CW = "rotate_cw"   # Rotating clockwise
    ROTATE_CCW = "rotate_ccw" # Rotating counter-clockwise
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    PINCH = "pinch"           # Thumb and index together
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


@dataclass
class FingerTip:
    """Represents a single fingertip position."""
    x: int
    y: int
    z: float  # Depth (0-1, closer to camera = lower)
    finger_id: int  # 0=thumb, 1=index, 2=middle, 3=ring, 4=pinky
    is_extended: bool
    confidence: float


@dataclass
class HandState:
    """Complete state of a detected hand."""
    fingertips: List[FingerTip]
    palm_center: Tuple[int, int]
    palm_normal: Tuple[float, float, float]  # Direction palm is facing
    wrist: Tuple[int, int]
    is_left: bool
    gesture: GestureType
    rotation_angle: float  # For dial control
    confidence: float


class MonicaHandController:
    """
    Advanced hand and fingertip detection with gesture recognition.
    Optimized for:
    - Precise fingertip detection for keyboard
    - Dial rotation gestures
    - Alarm trigger gestures
    """
    
    # Finger landmark indices in MediaPipe
    FINGER_TIPS = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky tips
    FINGER_PIPS = [3, 6, 10, 14, 18]  # PIP joints
    FINGER_MCPS = [2, 5, 9, 13, 17]   # MCP joints (knuckles)
    
    def __init__(self):
        self.enabled = True
        self.hands: List[HandState] = []
        
        # MediaPipe setup
        self._hand_landmarker = None
        self._use_tasks_api = False
        
        if HAS_MEDIAPIPE and _HandLandmarker is not None:
            # New Tasks API (mediapipe >= 0.10.20)
            try:
                import os
                model_path = os.path.join(
                    os.path.dirname(__file__), '..', '..', 'models', 'hand_landmarker.task'
                )
                model_path = os.path.abspath(model_path)
                if os.path.exists(model_path):
                    options = _HandLandmarkerOptions(
                        base_options=_BaseOptions(model_asset_path=model_path),
                        running_mode=_VisionRunningMode.IMAGE,
                        num_hands=2,
                        min_hand_detection_confidence=0.7,
                        min_tracking_confidence=0.5,
                    )
                    self._hand_landmarker = _HandLandmarker.create_from_options(options)
                    self._use_tasks_api = True
                    print("[HandController] Using MediaPipe Tasks API")
                else:
                    print(f"[WARN] Hand landmarker model not found: {model_path}")
            except Exception as e:
                print(f"[WARN] Tasks API init failed: {e}")
        
        if not self._hand_landmarker and HAS_MEDIAPIPE:
            # Fallback: legacy solutions API
            try:
                self._hand_landmarker = mp.solutions.hands.Hands(
                    static_image_mode=False,
                    max_num_hands=2,
                    min_detection_confidence=0.7,
                    min_tracking_confidence=0.5,
                    model_complexity=0
                )
                self._use_tasks_api = False
                print("[HandController] Using legacy MediaPipe solutions API")
            except (AttributeError, Exception) as e:
                print(f"[WARN] Legacy MediaPipe not available: {e}")
        
        # Gesture tracking
        self.prev_hand_positions: Dict[str, List[Tuple[int, int]]] = {}
        self.rotation_history: List[float] = []
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.3  # Seconds between gesture triggers
        
        # Dial interaction
        self.dial_center: Optional[Tuple[int, int]] = None
        self.dial_radius: int = 100
        self.dial_active = False
        self.dial_start_angle: float = 0
        self.dial_current_angle: float = 0
        
        # Alarm state
        self.alarm_triggered = False
        self.alarm_trigger_time = 0
        
        # Visualization settings
        self.show_landmarks = True   # Show skeleton by default
        self.show_fingertips = True
        self.fingertip_color = (0, 255, 255)  # Cyan
        self.fingertip_size = 10
        
        print("[HandController] Initialized - Fingertip precision mode")
    
    def set_dial_position(self, center: Tuple[int, int], radius: int):
        """Set the dial's position for gesture interaction."""
        self.dial_center = center
        self.dial_radius = radius
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[HandState]]:
        """
        Process frame for hand detection.
        Returns annotated frame and list of detected hands.
        """
        if not self.enabled or not HAS_MEDIAPIPE or self._hand_landmarker is None:
            return frame, []
        
        h, w = frame.shape[:2]
        
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Detect hands using the appropriate API
        hand_landmarks_list = []
        handedness_list = []
        
        if self._use_tasks_api:
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = self._hand_landmarker.detect(mp_image)
            if result.hand_landmarks:
                for lm_list in result.hand_landmarks:
                    hand_landmarks_list.append(_LandmarkListWrapper(lm_list))
            if result.handedness:
                for hd in result.handedness:
                    handedness_list.append(hd)
        else:
            # Legacy solutions API
            results = self._hand_landmarker.process(rgb_frame)
            if results.multi_hand_landmarks:
                for lm in results.multi_hand_landmarks:
                    hand_landmarks_list.append(lm)
            if hasattr(results, 'multi_handedness') and results.multi_handedness:
                handedness_list = results.multi_handedness
        
        self.hands = []
        
        for idx, hand_landmarks in enumerate(hand_landmarks_list):
            # Determine handedness
            is_left = False
            confidence = 0.5
            if idx < len(handedness_list):
                hd = handedness_list[idx]
                if self._use_tasks_api:
                    # Tasks API: list of Category objects
                    if hd:
                        is_left = hd[0].category_name == "Left"
                        confidence = hd[0].score
                else:
                    # Legacy API
                    cls = hd.classification[0]
                    is_left = cls.label == "Left"
                    confidence = cls.score
            
            # Extract fingertips
            fingertips = self._extract_fingertips(hand_landmarks, w, h, is_left)
            
            # Get palm center
            palm_center = self._get_palm_center(hand_landmarks, w, h)
            
            # Get wrist position
            wrist = (
                int(hand_landmarks.landmark[0].x * w),
                int(hand_landmarks.landmark[0].y * h)
            )
            
            # Detect gesture
            gesture = self._detect_gesture(hand_landmarks, fingertips, is_left)
            
            # Calculate rotation angle for dial
            rotation_angle = self._calculate_rotation(hand_landmarks, w, h)
            
            # Create hand state
            hand_state = HandState(
                fingertips=fingertips,
                palm_center=palm_center,
                palm_normal=(0, 0, 1),  # Simplified
                wrist=wrist,
                is_left=is_left,
                gesture=gesture,
                rotation_angle=rotation_angle,
                confidence=confidence
            )
            self.hands.append(hand_state)
            
            # Check dial interaction
            self._check_dial_interaction(hand_state)
            
            # Draw skeleton if enabled
            if self.show_landmarks:
                self._draw_hand_skeleton(frame, hand_landmarks, w, h)
            
            # Always draw fingertips (subtle)
            if self.show_fingertips:
                frame = self._draw_fingertips(frame, fingertips)
        
        return frame, self.hands

    def _draw_hand_skeleton(self, frame: np.ndarray, landmarks, w: int, h: int):
        """Draw hand skeleton (bones + joint dots) on frame."""
        pts = []
        for lm in landmarks.landmark:
            px, py = int(lm.x * w), int(lm.y * h)
            pts.append((px, py))
        
        # Draw bones (connections)
        for (a, b) in HAND_CONNECTIONS:
            if a < len(pts) and b < len(pts):
                cv2.line(frame, pts[a], pts[b], (0, 255, 0), 2, cv2.LINE_AA)
        
        # Draw joint dots
        for (px, py) in pts:
            cv2.circle(frame, (px, py), 4, (0, 200, 255), -1, cv2.LINE_AA)
            cv2.circle(frame, (px, py), 6, (0, 255, 0), 1, cv2.LINE_AA)
    
    def _extract_fingertips(self, landmarks, w: int, h: int, is_left: bool) -> List[FingerTip]:
        """Extract precise fingertip positions."""
        fingertips = []
        
        for i, tip_idx in enumerate(self.FINGER_TIPS):
            tip = landmarks.landmark[tip_idx]
            pip = landmarks.landmark[self.FINGER_PIPS[i]] if i > 0 else landmarks.landmark[2]
            mcp = landmarks.landmark[self.FINGER_MCPS[i]] if i > 0 else landmarks.landmark[1]
            
            # Check if finger is extended (more sensitive detection)
            if i == 0:  # Thumb
                # Thumb is extended if tip is far from palm
                is_extended = self._is_thumb_extended(landmarks, is_left)
            else:
                # Other fingers: tip should be above PIP (in y)
                # Lower threshold for more sensitive detection
                is_extended = tip.y < pip.y - 0.01  # More sensitive
            
            fingertip = FingerTip(
                x=int(tip.x * w),
                y=int(tip.y * h),
                z=tip.z,
                finger_id=i,
                is_extended=is_extended,
                confidence=1.0 - abs(tip.z)  # Closer = higher confidence
            )
            fingertips.append(fingertip)
        
        return fingertips
    
    def _is_thumb_extended(self, landmarks, is_left: bool) -> bool:
        """Check if thumb is extended (more sensitive)."""
        thumb_tip = landmarks.landmark[4]
        thumb_ip = landmarks.landmark[3]
        thumb_mcp = landmarks.landmark[2]
        index_mcp = landmarks.landmark[5]

        # Thumb is extended if tip is far from index MCP
        # Lower threshold for more sensitive detection
        if is_left:
            return thumb_tip.x > thumb_ip.x + 0.02  # More sensitive
        else:
            return thumb_tip.x < thumb_ip.x - 0.02  # More sensitive
    
    def _get_palm_center(self, landmarks, w: int, h: int) -> Tuple[int, int]:
        """Calculate palm center from landmarks."""
        # Average of wrist and MCP joints
        palm_landmarks = [0, 5, 9, 13, 17]  # Wrist + MCPs
        x_sum = sum(landmarks.landmark[i].x for i in palm_landmarks)
        y_sum = sum(landmarks.landmark[i].y for i in palm_landmarks)
        
        return (
            int(x_sum / len(palm_landmarks) * w),
            int(y_sum / len(palm_landmarks) * h)
        )
    
    def _detect_gesture(self, landmarks, fingertips: List[FingerTip], is_left: bool) -> GestureType:
        """Detect hand gesture."""
        extended = [ft.is_extended for ft in fingertips]
        num_extended = sum(extended)
        
        # Fist - no fingers extended
        if num_extended == 0:
            return GestureType.FIST
        
        # Open palm - all fingers extended
        if num_extended == 5:
            return GestureType.OPEN_PALM
        
        # Point - only index extended
        if extended[1] and not extended[2] and not extended[3] and not extended[4]:
            return GestureType.POINT
        
        # Thumbs up - only thumb extended, hand vertical
        if extended[0] and num_extended == 1:
            thumb_tip = landmarks.landmark[4]
            wrist = landmarks.landmark[0]
            if thumb_tip.y < wrist.y - 0.1:
                return GestureType.THUMBS_UP
            elif thumb_tip.y > wrist.y + 0.1:
                return GestureType.THUMBS_DOWN
        
        # Pinch - thumb and index close together
        thumb_tip = fingertips[0]
        index_tip = fingertips[1]
        dist = math.sqrt((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)
        if dist < 30:
            return GestureType.PINCH
        
        return GestureType.NONE
    
    def _calculate_rotation(self, landmarks, w: int, h: int) -> float:
        """Calculate hand rotation angle for dial control."""
        # Use index finger direction relative to wrist
        wrist = landmarks.landmark[0]
        index_mcp = landmarks.landmark[5]
        index_tip = landmarks.landmark[8]
        
        # Vector from wrist to index tip
        dx = index_tip.x - wrist.x
        dy = index_tip.y - wrist.y
        
        angle = math.degrees(math.atan2(dy, dx))
        return angle
    
    def _check_dial_interaction(self, hand: HandState):
        """Check if hand is interacting with dial."""
        if self.dial_center is None:
            return
        
        # Check if index fingertip is near dial
        index_tip = hand.fingertips[1]
        dist = math.sqrt(
            (index_tip.x - self.dial_center[0])**2 + 
            (index_tip.y - self.dial_center[1])**2
        )
        
        if dist < self.dial_radius * 1.5:
            self.dial_active = True
            
            # Calculate angle from dial center to fingertip
            dx = index_tip.x - self.dial_center[0]
            dy = index_tip.y - self.dial_center[1]
            angle = math.degrees(math.atan2(dy, dx))
            
            if not hasattr(self, '_prev_dial_angle'):
                self._prev_dial_angle = angle
            
            # Calculate rotation delta
            delta = angle - self._prev_dial_angle
            
            # Handle wrap-around
            if delta > 180:
                delta -= 360
            elif delta < -180:
                delta += 360
            
            self.dial_current_angle += delta
            self._prev_dial_angle = angle
            
            # Check for alarm trigger (fast rotation to the right)
            self.rotation_history.append(delta)
            if len(self.rotation_history) > 10:
                self.rotation_history.pop(0)
            
            # If consistent rightward rotation, trigger alarm
            if len(self.rotation_history) >= 5:
                avg_rotation = sum(self.rotation_history[-5:]) / 5
                if avg_rotation > 8:  # Fast clockwise rotation
                    current_time = time.time()
                    if current_time - self.alarm_trigger_time > 2.0:  # Cooldown
                        self.alarm_triggered = True
                        self.alarm_trigger_time = current_time
                        print("[HandController] [ALERT] ALARM TRIGGERED by dial rotation!")
        else:
            self.dial_active = False
            self._prev_dial_angle = None
    
    def _draw_fingertips(self, frame: np.ndarray, fingertips: List[FingerTip]) -> np.ndarray:
        """Draw prominent fingertip indicators with enhanced visibility."""
        for ft in fingertips:
            if ft.is_extended:
                # Multi-layer glow effect for better visibility
                # Outermost glow (largest)
                cv2.circle(frame, (ft.x, ft.y), self.fingertip_size + 10,
                          (255, 255, 0), 1, cv2.LINE_AA)
                cv2.circle(frame, (ft.x, ft.y), self.fingertip_size + 7,
                          (255, 200, 0), 2, cv2.LINE_AA)
                # Middle glow
                cv2.circle(frame, (ft.x, ft.y), self.fingertip_size + 4,
                          (255, 150, 0), 2, cv2.LINE_AA)
                # Inner bright ring
                cv2.circle(frame, (ft.x, ft.y), self.fingertip_size,
                          self.fingertip_color, -1, cv2.LINE_AA)
                # Bright center core
                cv2.circle(frame, (ft.x, ft.y), 5,
                          (255, 255, 255), -1, cv2.LINE_AA)
                # Super bright center point
                cv2.circle(frame, (ft.x, ft.y), 2,
                          (255, 255, 255), -1, cv2.LINE_AA)

                # Add fingertip label for index finger (most used for keyboard)
                if ft.finger_id == 1:  # Index finger
                    cv2.putText(frame, "CLICK", (ft.x - 20, ft.y - 25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

        return frame
    
    def get_index_fingertip(self, hand_index: int = 0) -> Optional[Tuple[int, int]]:
        """Get index fingertip position for the specified hand."""
        if hand_index < len(self.hands):
            index_tip = self.hands[hand_index].fingertips[1]
            if index_tip.is_extended:
                return (index_tip.x, index_tip.y)
        return None
    
    def get_all_extended_fingertips(self) -> List[Tuple[int, int]]:
        """Get all extended fingertip positions."""
        tips = []
        for hand in self.hands:
            for ft in hand.fingertips:
                if ft.is_extended:
                    tips.append((ft.x, ft.y))
        return tips
    
    def is_alarm_triggered(self) -> bool:
        """Check if alarm was triggered and reset flag."""
        if self.alarm_triggered:
            self.alarm_triggered = False
            return True
        return False
    
    def get_dial_value(self) -> float:
        """Get dial value (0.0 to 1.0) based on rotation."""
        # Normalize angle to 0-1 range
        normalized = (self.dial_current_angle % 360) / 360
        return max(0.0, min(1.0, normalized))


# Singleton
_controller: Optional[MonicaHandController] = None

def get_hand_controller() -> MonicaHandController:
    global _controller
    if _controller is None:
        _controller = MonicaHandController()
    return _controller


if __name__ == "__main__":
    # Test with webcam
    cap = cv2.VideoCapture(0)
    controller = MonicaHandController()
    controller.show_landmarks = True
    controller.set_dial_position((320, 240), 100)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame, hands = controller.process_frame(frame)
        
        # Draw dial area
        if controller.dial_center:
            color = (0, 255, 0) if controller.dial_active else (100, 100, 100)
            cv2.circle(frame, controller.dial_center, controller.dial_radius, color, 2)
            
            # Draw dial value
            value = controller.get_dial_value()
            cv2.putText(frame, f"Dial: {value:.2f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Show alarm status
        if controller.is_alarm_triggered():
            cv2.putText(frame, "ALARM!", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        
        cv2.imshow("Hand Controller Test", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
