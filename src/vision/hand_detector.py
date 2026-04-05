"""
Monica Hand Detector
Provides hand detection and tracking using MediaPipe.
Fallback module for vision system.

Author: Monica AI
Date: December 2025
"""

import cv2
import numpy as np
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass

# Try to import MediaPipe
HAS_MEDIAPIPE = False
try:
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except ImportError:
    print("[HAND] MediaPipe not available - hand detection will be limited")


@dataclass
class HandLandmark:
    """A single hand landmark point."""
    x: float
    y: float
    z: float
    visibility: float = 1.0


@dataclass
class Hand:
    """Detected hand with landmarks."""
    landmarks: List[HandLandmark]
    handedness: str  # 'Left' or 'Right'
    confidence: float
    bbox: Tuple[int, int, int, int] = None  # x, y, w, h
    
    @property
    def wrist(self) -> HandLandmark:
        return self.landmarks[0] if self.landmarks else None
    
    @property
    def thumb_tip(self) -> HandLandmark:
        return self.landmarks[4] if len(self.landmarks) > 4 else None
    
    @property
    def index_tip(self) -> HandLandmark:
        return self.landmarks[8] if len(self.landmarks) > 8 else None
    
    @property
    def middle_tip(self) -> HandLandmark:
        return self.landmarks[12] if len(self.landmarks) > 12 else None
    
    @property
    def ring_tip(self) -> HandLandmark:
        return self.landmarks[16] if len(self.landmarks) > 16 else None
    
    @property
    def pinky_tip(self) -> HandLandmark:
        return self.landmarks[20] if len(self.landmarks) > 20 else None
    
    def get_fingertips(self) -> List[HandLandmark]:
        """Get all fingertip landmarks."""
        tips = []
        for idx in [4, 8, 12, 16, 20]:
            if len(self.landmarks) > idx:
                tips.append(self.landmarks[idx])
        return tips
    
    def get_center(self) -> Tuple[float, float]:
        """Get center of hand."""
        if not self.landmarks:
            return (0, 0)
        
        x_sum = sum(lm.x for lm in self.landmarks)
        y_sum = sum(lm.y for lm in self.landmarks)
        n = len(self.landmarks)
        
        return (x_sum / n, y_sum / n)


class HandDetector:
    """
    Hand detector using MediaPipe Hands.
    """
    
    # Landmark indices
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20
    
    def __init__(self,
                 max_hands: int = 2,
                 min_detection_confidence: float = 0.7,  # Balanced for speed
                 min_tracking_confidence: float = 0.5,   # Lower for better responsiveness
                 model_complexity: int = 0):  # Use simpler model for speed
        """
        Initialize hand detector.

        Args:
            max_hands: Maximum number of hands to detect
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
            model_complexity: Model complexity (0, 1, or 2)
        """
        self.max_hands = max_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence

        self.hands = None
        self.mp_hands = None
        self.mp_draw = None

        # Detection mode
        self.use_full_frame_mode = False

        # Smoothing for stability (reduces jitter)
        self.prev_landmarks = {}  # Store previous landmarks per hand
        self.smoothing_factor = 0.2  # Lower = less lag, more responsive (0-1)

        # Adaptive smoothing based on movement speed
        self.use_adaptive_smoothing = True
        self.prev_positions = {}  # For velocity calculation
        
        if HAS_MEDIAPIPE:
            self.mp_hands = mp.solutions.hands
            self.mp_draw = mp.solutions.drawing_utils
            
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=max_hands,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
                model_complexity=model_complexity
            )
            
            print(f"[HAND] Hand detector initialized (accuracy mode, max_hands={max_hands})")
        else:
            print("[HAND] Hand detector running in fallback mode")
    
    def use_full_frame(self):
        """Enable full frame detection mode."""
        self.use_full_frame_mode = True
    
    def use_roi(self):
        """Enable ROI (region of interest) detection mode."""
        self.use_full_frame_mode = False
    
    def detect(self, frame: np.ndarray) -> List[Hand]:
        """
        Detect hands in a frame.
        
        Args:
            frame: BGR image
            
        Returns:
            List of detected Hand objects
        """
        if not HAS_MEDIAPIPE or self.hands is None:
            return []
        
        # Convert to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process
        results = self.hands.process(rgb)
        
        detected_hands = []
        
        if results.multi_hand_landmarks:
            h, w = frame.shape[:2]
            
            for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                # Get handedness
                handedness = "Right"
                if results.multi_handedness:
                    handedness = results.multi_handedness[idx].classification[0].label
                    confidence = results.multi_handedness[idx].classification[0].score
                else:
                    confidence = 0.9
                
                # Convert landmarks
                landmarks = []
                x_coords = []
                y_coords = []
                
                for i, lm in enumerate(hand_landmarks.landmark):
                    # Apply adaptive smoothing to reduce jitter while maintaining responsiveness
                    x_val = lm.x
                    y_val = lm.y
                    z_val = lm.z

                    # Adaptive smoothing based on movement speed
                    hand_key = f"{handedness}_{i}"
                    if hand_key in self.prev_landmarks:
                        prev = self.prev_landmarks[hand_key]

                        # Calculate movement distance (velocity proxy)
                        dx = abs(x_val - prev[0])
                        dy = abs(y_val - prev[1])
                        movement = (dx * dx + dy * dy) ** 0.5

                        # Adaptive smoothing: less smoothing for fast movements
                        if self.use_adaptive_smoothing:
                            # If moving fast, use less smoothing (more responsive)
                            # If moving slow, use more smoothing (less jitter)
                            if movement > 0.05:  # Fast movement threshold
                                adaptive_factor = 0.1  # Very responsive
                            elif movement > 0.02:  # Medium movement
                                adaptive_factor = 0.15
                            else:  # Slow or stationary
                                adaptive_factor = self.smoothing_factor
                        else:
                            adaptive_factor = self.smoothing_factor

                        x_val = prev[0] * adaptive_factor + x_val * (1 - adaptive_factor)
                        y_val = prev[1] * adaptive_factor + y_val * (1 - adaptive_factor)
                        z_val = prev[2] * adaptive_factor + z_val * (1 - adaptive_factor)

                    self.prev_landmarks[hand_key] = (x_val, y_val, z_val)
                    
                    landmarks.append(HandLandmark(
                        x=x_val,
                        y=y_val,
                        z=z_val,
                        visibility=getattr(lm, 'visibility', 1.0)
                    ))
                    x_coords.append(int(x_val * w))
                    y_coords.append(int(y_val * h))
                
                # Calculate bounding box
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                padding = 20
                bbox = (
                    max(0, x_min - padding),
                    max(0, y_min - padding),
                    min(w, x_max - x_min + 2*padding),
                    min(h, y_max - y_min + 2*padding)
                )
                
                detected_hands.append(Hand(
                    landmarks=landmarks,
                    handedness=handedness,
                    confidence=confidence,
                    bbox=bbox
                ))
        
        return detected_hands
    
    def draw_hands(self, frame: np.ndarray, hands: List[Hand] = None,
                   draw_landmarks: bool = True,
                   draw_connections: bool = True,
                   draw_bbox: bool = False) -> np.ndarray:
        """
        Draw detected hands on frame.
        
        Args:
            frame: BGR image
            hands: List of Hand objects (if None, will detect)
            draw_landmarks: Draw landmark points
            draw_connections: Draw connections between landmarks
            draw_bbox: Draw bounding box
            
        Returns:
            Frame with hands drawn
        """
        if hands is None:
            hands = self.detect(frame)
        
        if not HAS_MEDIAPIPE:
            return frame
        
        h, w = frame.shape[:2]
        output = frame.copy()
        
        for hand in hands:
            # Draw bounding box
            if draw_bbox and hand.bbox:
                x, y, bw, bh = hand.bbox
                color = (0, 255, 0) if hand.handedness == "Right" else (255, 0, 0)
                cv2.rectangle(output, (x, y), (x + bw, y + bh), color, 2)
                cv2.putText(output, f"{hand.handedness} ({hand.confidence:.2f})",
                           (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Draw landmarks and connections
            if draw_landmarks or draw_connections:
                # Convert to MediaPipe format for drawing
                landmark_list = []
                for lm in hand.landmarks:
                    landmark_list.append((int(lm.x * w), int(lm.y * h)))
                
                # Draw connections
                if draw_connections:
                    connections = [
                        (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
                        (0, 5), (5, 6), (6, 7), (7, 8),  # Index
                        (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
                        (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
                        (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
                        (5, 9), (9, 13), (13, 17)  # Palm
                    ]
                    
                    for start, end in connections:
                        if start < len(landmark_list) and end < len(landmark_list):
                            cv2.line(output, landmark_list[start], landmark_list[end],
                                    (0, 255, 0), 2)
                
                # Draw landmarks
                if draw_landmarks:
                    for i, (x, y) in enumerate(landmark_list):
                        # Fingertips get special glowing effect
                        if i in [4, 8, 12, 16, 20]:
                            # GLOWING FINGERTIP - ready to click!
                            # Outer glow (cyan)
                            cv2.circle(output, (x, y), 18, (255, 255, 0), 2, cv2.LINE_AA)
                            cv2.circle(output, (x, y), 14, (255, 200, 0), 2, cv2.LINE_AA)
                            cv2.circle(output, (x, y), 10, (255, 150, 0), 2, cv2.LINE_AA)
                            # Inner bright core
                            cv2.circle(output, (x, y), 6, (255, 255, 255), -1, cv2.LINE_AA)
                            cv2.circle(output, (x, y), 4, (255, 255, 0), -1, cv2.LINE_AA)
                        else:
                            # Regular joint - smaller green dot
                            cv2.circle(output, (x, y), 4, (0, 255, 0), -1, cv2.LINE_AA)
        
        return output
    
    def get_finger_states(self, hand: Hand) -> Dict[str, bool]:
        """
        Determine which fingers are extended.
        
        Args:
            hand: Hand object
            
        Returns:
            Dictionary with finger states (True = extended)
        """
        if not hand.landmarks or len(hand.landmarks) < 21:
            return {}
        
        # Get relevant landmarks
        wrist = hand.landmarks[0]
        
        # Thumb (compare tip to IP joint, considering handedness)
        thumb_tip = hand.landmarks[4]
        thumb_ip = hand.landmarks[3]
        thumb_mcp = hand.landmarks[2]
        
        # For thumb, check if tip is further from palm than IP
        if hand.handedness == "Right":
            thumb_extended = thumb_tip.x < thumb_ip.x
        else:
            thumb_extended = thumb_tip.x > thumb_ip.x
        
        # Other fingers (compare tip Y to PIP Y - lower Y = extended)
        fingers = {
            'thumb': thumb_extended,
            'index': hand.landmarks[8].y < hand.landmarks[6].y,
            'middle': hand.landmarks[12].y < hand.landmarks[10].y,
            'ring': hand.landmarks[16].y < hand.landmarks[14].y,
            'pinky': hand.landmarks[20].y < hand.landmarks[18].y
        }
        
        return fingers
    
    def count_fingers(self, hand: Hand) -> int:
        """Count number of extended fingers."""
        states = self.get_finger_states(hand)
        return sum(1 for v in states.values() if v)
    
    def get_gesture(self, hand: Hand) -> str:
        """
        Recognize basic hand gestures.
        
        Args:
            hand: Hand object
            
        Returns:
            Gesture name
        """
        fingers = self.get_finger_states(hand)
        
        if not fingers:
            return "unknown"
        
        count = sum(1 for v in fingers.values() if v)
        
        # Fist
        if count == 0:
            return "fist"
        
        # Open palm
        if count == 5:
            return "open"
        
        # Thumbs up
        if fingers.get('thumb') and count == 1:
            return "thumbs_up"
        
        # Peace sign
        if fingers.get('index') and fingers.get('middle') and count == 2:
            return "peace"
        
        # Pointing
        if fingers.get('index') and count == 1:
            return "pointing"
        
        # OK sign (thumb and index touching)
        if hand.thumb_tip and hand.index_tip:
            dist = ((hand.thumb_tip.x - hand.index_tip.x)**2 + 
                   (hand.thumb_tip.y - hand.index_tip.y)**2)**0.5
            if dist < 0.05 and count <= 3:
                return "ok"
        
        # Rock sign
        if fingers.get('index') and fingers.get('pinky') and count == 2:
            return "rock"
        
        return f"fingers_{count}"
    
    def close(self):
        """Release resources."""
        if self.hands:
            self.hands.close()
            self.hands = None


# Singleton instance
_detector = None

def get_hand_detector(**kwargs) -> HandDetector:
    """Get the singleton HandDetector instance."""
    global _detector
    if _detector is None:
        _detector = HandDetector(**kwargs)
    return _detector


def get_index_fingertip_position(hand: Hand, frame_width: int, frame_height: int) -> Tuple[int, int]:
    """
    Get the pixel position of the index fingertip.
    
    Args:
        hand: Hand object
        frame_width: Width of the frame
        frame_height: Height of the frame
        
    Returns:
        (x, y) pixel position of index fingertip
    """
    if hand and hand.index_tip:
        x = int(hand.index_tip.x * frame_width)
        y = int(hand.index_tip.y * frame_height)
        return (x, y)
    return None


def is_pinching(hand: Hand, threshold: float = 0.05) -> bool:
    """
    Check if thumb and index finger are pinching (close together).
    Used for clicking/selecting.
    
    Args:
        hand: Hand object
        threshold: Distance threshold for pinch detection
        
    Returns:
        True if pinching
    """
    if not hand or not hand.thumb_tip or not hand.index_tip:
        return False
    
    dx = hand.thumb_tip.x - hand.index_tip.x
    dy = hand.thumb_tip.y - hand.index_tip.y
    distance = (dx*dx + dy*dy) ** 0.5
    
    return distance < threshold


# Test
if __name__ == "__main__":
    print("Testing Hand Detector...")
    
    detector = HandDetector()
    
    # Test with webcam
    cap = cv2.VideoCapture(0)
    
    print("Press 'q' to quit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect hands
        hands = detector.detect(frame)
        
        # Draw hands
        frame = detector.draw_hands(frame, hands, draw_bbox=True)
        
        # Show info
        for i, hand in enumerate(hands):
            gesture = detector.get_gesture(hand)
            fingers = detector.count_fingers(hand)
            cv2.putText(frame, f"Hand {i+1}: {gesture} ({fingers} fingers)",
                       (10, 30 + i*30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow("Hand Detector", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    detector.close()
    
    print("[OK] Hand Detector test complete!")
