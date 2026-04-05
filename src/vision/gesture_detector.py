"""
Monica Gesture Detector
Provides gesture recognition including finger counting.
Works with the hand detector module.

Author: Monica AI
Date: December 2025
"""

import cv2
import numpy as np
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass

# Try to import hand detector
try:
    from hand_detector import HandDetector, Hand, get_hand_detector
    HAS_HAND_DETECTOR = True
except ImportError:
    HAS_HAND_DETECTOR = False
    print("[GESTURE] Hand detector not available")


@dataclass
class Gesture:
    """Recognized gesture."""
    name: str
    confidence: float
    hand: str  # 'left', 'right', or 'both'
    finger_count: int = 0
    metadata: Dict[str, Any] = None


class GestureDetector:
    """
    Gesture detector with finger counting and gesture recognition.
    """
    
    # Gesture definitions
    GESTURES = {
        'fist': {'fingers': 0, 'description': 'Closed fist'},
        'open': {'fingers': 5, 'description': 'Open palm'},
        'thumbs_up': {'fingers': 1, 'thumb': True, 'description': 'Thumbs up'},
        'thumbs_down': {'fingers': 1, 'thumb': True, 'inverted': True, 'description': 'Thumbs down'},
        'peace': {'fingers': 2, 'index': True, 'middle': True, 'description': 'Peace sign'},
        'pointing': {'fingers': 1, 'index': True, 'description': 'Pointing'},
        'ok': {'thumb_index_touch': True, 'description': 'OK sign'},
        'rock': {'fingers': 2, 'index': True, 'pinky': True, 'description': 'Rock sign'},
        'call': {'fingers': 2, 'thumb': True, 'pinky': True, 'description': 'Call me'},
        'one': {'fingers': 1, 'index': True, 'description': 'Number one'},
        'two': {'fingers': 2, 'description': 'Number two'},
        'three': {'fingers': 3, 'description': 'Number three'},
        'four': {'fingers': 4, 'description': 'Number four'},
        'five': {'fingers': 5, 'description': 'Number five'},
    }
    
    def __init__(self, hand_detector: HandDetector = None):
        """
        Initialize gesture detector.
        
        Args:
            hand_detector: HandDetector instance (will create one if not provided)
        """
        if hand_detector:
            self.hand_detector = hand_detector
        elif HAS_HAND_DETECTOR:
            self.hand_detector = get_hand_detector()
        else:
            self.hand_detector = None
            print("[GESTURE] Running without hand detector")
        
        # Gesture history for smoothing
        self.gesture_history: List[str] = []
        self.history_size = 5
        
        print("[GESTURE] Gesture detector initialized")
    
    def detect_gestures(self, frame: np.ndarray) -> List[Gesture]:
        """
        Detect gestures in a frame.
        
        Args:
            frame: BGR image
            
        Returns:
            List of detected Gesture objects
        """
        if not self.hand_detector:
            return []
        
        # Detect hands
        hands = self.hand_detector.detect(frame)
        
        gestures = []
        for hand in hands:
            gesture = self._recognize_gesture(hand)
            if gesture:
                gestures.append(gesture)
        
        return gestures
    
    def _recognize_gesture(self, hand: Hand) -> Optional[Gesture]:
        """Recognize gesture from a hand."""
        if not self.hand_detector:
            return None
        
        # Get finger states
        finger_states = self.hand_detector.get_finger_states(hand)
        if not finger_states:
            return None
        
        # Count extended fingers
        finger_count = sum(1 for v in finger_states.values() if v)
        
        # Get gesture name
        gesture_name = self.hand_detector.get_gesture(hand)
        
        # Calculate confidence based on clarity of gesture
        confidence = hand.confidence
        
        return Gesture(
            name=gesture_name,
            confidence=confidence,
            hand=hand.handedness.lower(),
            finger_count=finger_count,
            metadata={'finger_states': finger_states}
        )
    
    def count_fingers(self, frame: np.ndarray) -> Dict[str, int]:
        """
        Count fingers in frame.
        
        Args:
            frame: BGR image
            
        Returns:
            Dictionary with finger counts per hand
        """
        if not self.hand_detector:
            return {}
        
        hands = self.hand_detector.detect(frame)
        
        counts = {}
        for hand in hands:
            count = self.hand_detector.count_fingers(hand)
            counts[hand.handedness.lower()] = count
        
        return counts
    
    def get_total_fingers(self, frame: np.ndarray) -> int:
        """Get total number of extended fingers across all hands."""
        counts = self.count_fingers(frame)
        return sum(counts.values())
    
    def draw_gestures(self, frame: np.ndarray, 
                      gestures: List[Gesture] = None) -> np.ndarray:
        """
        Draw gesture information on frame.
        
        Args:
            frame: BGR image
            gestures: List of Gesture objects (will detect if None)
            
        Returns:
            Frame with gesture info drawn
        """
        if gestures is None:
            gestures = self.detect_gestures(frame)
        
        output = frame.copy()
        
        # Draw gesture info
        y_offset = 30
        for gesture in gestures:
            text = f"{gesture.hand.title()}: {gesture.name} ({gesture.finger_count} fingers)"
            cv2.putText(output, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y_offset += 30
        
        # Draw hands if hand detector available
        if self.hand_detector:
            hands = self.hand_detector.detect(frame)
            output = self.hand_detector.draw_hands(output, hands)
        
        return output
    
    def get_smoothed_gesture(self, gesture_name: str) -> str:
        """
        Get smoothed gesture using history.
        Helps reduce flickering between gestures.
        """
        self.gesture_history.append(gesture_name)
        
        if len(self.gesture_history) > self.history_size:
            self.gesture_history.pop(0)
        
        # Return most common gesture in history
        if self.gesture_history:
            from collections import Counter
            counter = Counter(self.gesture_history)
            return counter.most_common(1)[0][0]
        
        return gesture_name
    
    def is_gesture(self, frame: np.ndarray, gesture_name: str) -> bool:
        """Check if a specific gesture is being made."""
        gestures = self.detect_gestures(frame)
        return any(g.name == gesture_name for g in gestures)
    
    def wait_for_gesture(self, cap, gesture_name: str, 
                         timeout: float = 10.0) -> bool:
        """
        Wait for a specific gesture.
        
        Args:
            cap: cv2.VideoCapture object
            gesture_name: Name of gesture to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if gesture was detected, False if timeout
        """
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            ret, frame = cap.read()
            if not ret:
                continue
            
            if self.is_gesture(frame, gesture_name):
                return True
            
            # Small delay
            cv2.waitKey(1)
        
        return False


# Singleton instance
_detector = None

def get_gesture_detector(**kwargs) -> GestureDetector:
    """Get the singleton GestureDetector instance."""
    global _detector
    if _detector is None:
        _detector = GestureDetector(**kwargs)
    return _detector


# Test
if __name__ == "__main__":
    print("Testing Gesture Detector...")
    
    detector = GestureDetector()
    
    # Test with webcam
    cap = cv2.VideoCapture(0)
    
    print("Press 'q' to quit")
    print("Show different gestures to test detection")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect and draw gestures
        gestures = detector.detect_gestures(frame)
        frame = detector.draw_gestures(frame, gestures)
        
        # Show total finger count
        total = detector.get_total_fingers(frame)
        cv2.putText(frame, f"Total fingers: {total}",
                   (10, frame.shape[0] - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        cv2.imshow("Gesture Detector", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    print("[OK] Gesture Detector test complete!")
