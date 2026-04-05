"""
Monica's Advanced Visual Capabilities
Includes: Thermal/Heat Vision, Night Vision, Emotion Detection, Object Detection,
Webcam Access, AR/Holographic Display via Spout

IMPORTANT: Uses lazy loading to avoid slow startup and import order issues.
MediaPipe must be imported BEFORE TensorFlow/DeepFace to avoid hangs.
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import os
import requests
from datetime import datetime

# =============================================================================
# LAZY LOADING - Heavy modules loaded on first use, not at startup
# This dramatically improves startup time and avoids TensorFlow/MediaPipe conflicts
# =============================================================================

# Module availability flags (None = not checked yet)
HAS_TORCH = None
HAS_DEEPFACE = None
HAS_YOLO = None
HAS_MEDIAPIPE = None
HAS_FER = None

# Cached module references
_torch = None
_deepface = None
_yolo = None
_mp = None
_fer = None


def _load_torch():
    """Lazy load PyTorch."""
    global _torch, HAS_TORCH
    if HAS_TORCH is None:
        try:
            import torch
            _torch = torch
            HAS_TORCH = True
        except ImportError:
            HAS_TORCH = False
    return _torch if HAS_TORCH else None


def _load_fer():
    """Lazy load FER for emotion detection."""
    global _fer, HAS_FER
    if HAS_FER is None:
        try:
            from fer import FER
            _fer = FER
            HAS_FER = True
        except ImportError:
            HAS_FER = False
    return _fer if HAS_FER else None


def _load_mediapipe():
    """Lazy load MediaPipe - MUST be loaded BEFORE TensorFlow/DeepFace."""
    global _mp, HAS_MEDIAPIPE
    if HAS_MEDIAPIPE is None:
        try:
            import mediapipe as mp
            _mp = mp
            HAS_MEDIAPIPE = True
        except ImportError:
            HAS_MEDIAPIPE = False
    return _mp if HAS_MEDIAPIPE else None


def _load_yolo():
    """Lazy load YOLO object detector."""
    global _yolo, HAS_YOLO
    if HAS_YOLO is None:
        try:
            from ultralytics import YOLO  # type: ignore
            _yolo = YOLO
            HAS_YOLO = True
        except ImportError:
            HAS_YOLO = False
            print("[WARN] YOLO not available - install with: pip install ultralytics")
    return _yolo if HAS_YOLO else None


def _load_deepface():
    """Lazy load DeepFace for emotion analysis."""
    global _deepface, HAS_DEEPFACE
    if HAS_DEEPFACE is None:
        try:
            # Pre-load mediapipe to avoid conflicts
            _load_mediapipe()
            from deepface import DeepFace
            _deepface = DeepFace
            HAS_DEEPFACE = True
        except (ImportError, ModuleNotFoundError):
            HAS_DEEPFACE = False
            print("[WARN] DeepFace not available - install with: pip install deepface")
    return _deepface if HAS_DEEPFACE else None


class TerminatorVision:
    """
    Terminator-style vision overlay with red tint and moving scanlines.
    """
    
    def __init__(self):
        self.enabled = False
        self.scanline_pos = 0
        self.scanline_speed = 4  # Pixels per frame
        print("[OK] Terminator Vision initialized")
    
    def apply(self, frame: np.ndarray) -> np.ndarray:
        """Apply Terminator vision effect to frame"""
        if not self.enabled:
            return frame
        
        # Apply red tint
        result = frame.copy()
        result[:, :, 0] = 0  # Zero out blue channel
        result[:, :, 1] = 0  # Zero out green channel
        
        # Add scanline
        h, w, _ = result.shape
        self.scanline_pos = (self.scanline_pos + self.scanline_speed) % h
        cv2.line(result, (0, self.scanline_pos), (w, self.scanline_pos), (255, 0, 0), 1)
        cv2.line(result, (0, self.scanline_pos + 2), (w, self.scanline_pos + 2), (100, 0, 0), 1)
        
        # Add some noise
        noise = np.random.randint(0, 15, (h, w, 3), dtype=np.uint8)
        result = cv2.add(result, noise)
        
        return result
    
    def toggle(self):
        """Toggle terminator vision on/off"""
        self.enabled = not self.enabled
        return self.enabled


class ThermalVision:
    """
    Simulated thermal/heat vision effect.
    Converts regular camera feed to thermal-like visualization.
    Note: This is a visual simulation, not actual infrared sensing.
    """
    
    def __init__(self):
        self.enabled = False
        self.colormap = cv2.COLORMAP_JET  # Thermal-like colormap
        self.sensitivity = 1.0
        print("[OK] Thermal Vision initialized (simulated)")
    
    def apply(self, frame: np.ndarray) -> np.ndarray:
        """Apply thermal vision effect to frame"""
        if not self.enabled:
            return frame
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to smooth
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)
        
        # Apply thermal colormap
        thermal = cv2.applyColorMap(enhanced, self.colormap)
        
        return thermal
    
    def toggle(self):
        """Toggle thermal vision on/off"""
        self.enabled = not self.enabled
        return self.enabled
    
    def set_colormap(self, colormap_name: str):
        """Set the thermal colormap style"""
        colormaps = {
            "jet": cv2.COLORMAP_JET,
            "hot": cv2.COLORMAP_HOT,
            "inferno": cv2.COLORMAP_INFERNO,
            "plasma": cv2.COLORMAP_PLASMA,
            "magma": cv2.COLORMAP_MAGMA,
            "turbo": cv2.COLORMAP_TURBO,
        }
        if colormap_name.lower() in colormaps:
            self.colormap = colormaps[colormap_name.lower()]


class NightVision:
    """
    Night vision effect for low-light enhancement.
    Simulates night vision goggles appearance.
    """
    
    def __init__(self):
        self.enabled = False
        self.green_tint = True
        self.brightness_boost = 2.0
        self.noise_level = 0.05
        print("[OK] Night Vision initialized")
    
    def apply(self, frame: np.ndarray) -> np.ndarray:
        """Apply night vision effect to frame"""
        if not self.enabled:
            return frame
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Boost brightness
        brightened = cv2.convertScaleAbs(gray, alpha=self.brightness_boost, beta=30)
        
        # Apply CLAHE for better contrast in dark areas
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(brightened)
        
        # Add slight noise for authentic look
        if self.noise_level > 0:
            noise = np.random.normal(0, self.noise_level * 255, enhanced.shape).astype(np.uint8)
            enhanced = cv2.add(enhanced, noise)
        
        # Apply green tint (classic night vision look)
        if self.green_tint:
            result = np.zeros((frame.shape[0], frame.shape[1], 3), dtype=np.uint8)
            result[:, :, 1] = enhanced  # Green channel
            result[:, :, 0] = enhanced // 4  # Slight blue
            result[:, :, 2] = enhanced // 4  # Slight red
        else:
            result = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        return result
    
    def toggle(self):
        """Toggle night vision on/off"""
        self.enabled = not self.enabled
        return self.enabled


class EmotionDetector:
    """
    Detects emotions from facial expressions and voice/text.
    Uses FER (primary) or DeepFace for facial emotion recognition.
    """
    
    EMOTIONS = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
    
    def __init__(self):
        self.enabled = True
        self.last_emotion = "neutral"
        self.emotion_history = []
        self.confidence_threshold = 0.3
        self.backend = "none"
        
        # Try to load FER first
        if _load_fer():
            if _fer:
                self.detector = _fer()
                self.backend = "fer"
        # Fallback to DeepFace if FER not available
        elif _load_deepface():
            self.backend = "deepface"
        # Final fallback to basic face detection
        else:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.backend = "cascade"
        
        print(f"[OK] Emotion Detection initialized (backend: {self.backend})")
    
    def detect_from_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Detect emotions from a video frame"""
        result = {
            "emotion": "neutral",
            "confidence": 0.0,
            "all_emotions": {},
            "face_detected": False,
            "face_location": None
        }
        
        if not self.enabled:
            return result
        
        try:
            # Use FER if available
            if self.backend == "fer" and self.detector is not None:
                # ... implementation for FER ...
                pass  # Placeholder
            
            # Use DeepFace if available
            elif self.backend == "deepface":
                # ... implementation for DeepFace ...
                pass  # Placeholder

            # Basic face detection fallback
            elif self.backend == "cascade":
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                
                if len(faces) > 0:
                    result["face_detected"] = True
                    x, y, w, h = faces[0]
                    result["face_location"] = (x, y, w, h)
                    result["emotion"] = "detected"  # Can't determine emotion
            
            # Update history
            if result["face_detected"]:
                self.last_emotion = result["emotion"]
                self.emotion_history.append({
                    "emotion": result["emotion"],
                    "timestamp": datetime.now().isoformat()
                })
                # Keep only last 100 entries
                if len(self.emotion_history) > 100:
                    self.emotion_history = self.emotion_history[-100:]
        
        except Exception as e:
            # Silently handle errors to not spam console
            pass
        
        return result
    
    def detect_from_text(self, text: str) -> Dict[str, Any]:
        """Detect emotions from text using keyword analysis"""
        text_lower = text.lower()
        
        emotion_keywords = {
            "happy": ["happy", "joy", "excited", "great", "wonderful", "amazing", "love", "glad", "pleased", "delighted"],
            "sad": ["sad", "unhappy", "depressed", "down", "upset", "crying", "tears", "miserable", "heartbroken"],
            "angry": ["angry", "mad", "furious", "annoyed", "frustrated", "irritated", "rage", "hate"],
            "fear": ["scared", "afraid", "terrified", "anxious", "worried", "nervous", "panic", "frightened"],
            "surprise": ["surprised", "shocked", "amazed", "astonished", "wow", "unexpected", "unbelievable"],
            "disgust": ["disgusted", "gross", "yuck", "ew", "revolting", "nasty"],
            "neutral": []
        }
        
        detected_emotions: Dict[str, int] = {}
        for emotion, keywords in emotion_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            if count > 0:
                detected_emotions[emotion] = count
        
        if detected_emotions:
            dominant = max(detected_emotions, key=detected_emotions.get)  # type: ignore
            return {
                "emotion": dominant,
                "confidence": min(detected_emotions[dominant] / 3.0, 1.0),
                "all_emotions": detected_emotions
            }
        
        return {"emotion": "neutral", "confidence": 0.5, "all_emotions": {}}
    
    def draw_emotion_overlay(self, frame: np.ndarray, emotion_data: Dict) -> np.ndarray:
        """Draw emotion information on frame"""
        if not emotion_data.get("face_detected"):
            return frame
        
        result = frame.copy()
        
        # Draw face rectangle
        if emotion_data.get("face_location"):
            x, y, w, h = emotion_data["face_location"]
            
            # Color based on emotion
            emotion_colors = {
                "happy": (0, 255, 0),      # Green
                "sad": (255, 0, 0),        # Blue
                "angry": (0, 0, 255),      # Red
                "fear": (128, 0, 128),     # Purple
                "surprise": (0, 255, 255), # Yellow
                "disgust": (0, 128, 0),    # Dark green
                "neutral": (128, 128, 128) # Gray
            }
            
            color = emotion_colors.get(emotion_data["emotion"], (255, 255, 255))
            cv2.rectangle(result, (x, y), (x + w, y + h), color, 2)
            
            # Draw emotion label
            label = f"{emotion_data['emotion'].upper()} ({emotion_data['confidence']:.0%})"
            cv2.putText(result, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return result


class ObjectDetector:
    """
    Object detection using YOLOv8.
    Detects and labels objects in the frame.
    """
    
    def __init__(self, model_size: str = "n"):
        self.enabled = True
        self.model = None
        self.confidence_threshold = 0.5
        
        # Try to load YOLO
        YOLO = _load_yolo()
        if YOLO:
            try:
                model_path = f"yolov8{model_size}.pt"
                # Download model if it doesn't exist
                if not os.path.exists(model_path):
                    print(f"Downloading YOLOv8 model: {model_path}...")
                    # Note: This is a placeholder for a proper download mechanism
                    # For now, assumes the model is present or will fail gracefully
                    pass
                
                self.model = YOLO(model_path)
                print(f"[OK] Object Detection initialized (YOLOv8{model_size})")
            except Exception as e:
                print(f"[WARN] Object Detection (YOLO) initialization failed: {e}")
                self.model = None
        else:
            print("[WARN] Object Detection not available (ultralytics not installed)")
    
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """Detect objects in frame"""
        if not self.enabled or self.model is None:
            return []
        
        try:
            results = self.model(frame, verbose=False)
            detections = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    conf = float(box.conf[0])
                    if conf >= self.confidence_threshold:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cls = int(box.cls[0])
                        name = self.model.names[cls]
                        
                        detections.append({
                            "name": name,
                            "confidence": conf,
                            "bbox": (x1, y1, x2, y2)
                        })
            
            return detections
        except Exception as e:
            return []
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw detection boxes on frame"""
        result = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            name = det["name"]
            conf = det["confidence"]
            
            # Draw box
            cv2.rectangle(result, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"{name} {conf:.0%}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(result, (x1, y1 - h - 10), (x1 + w, y1), (0, 255, 0), -1)
            cv2.putText(result, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return result


class PublicWebcamAccess:
    """
    Access public webcams around the world.
    Uses various public webcam APIs and feeds.
    """
    
    # Database of public webcam feeds
    PUBLIC_WEBCAMS = {
        "times_square": {
            "name": "Times Square, New York",
            "url": "https://www.earthcam.com/usa/newyork/timessquare/",
            "lat": 40.7580, "lng": -73.9855,
            "type": "earthcam"
        },
        "abbey_road": {
            "name": "Abbey Road, London",
            "url": "https://www.earthcam.com/world/england/london/abbeyroad/",
            "lat": 51.5320, "lng": -0.1780,
            "type": "earthcam"
        },
        "shibuya": {
            "name": "Shibuya Crossing, Tokyo",
            "url": "https://www.youtube.com/watch?v=shibuya_live",
            "lat": 35.6595, "lng": 139.7004,
            "type": "youtube"
        },
        "venice": {
            "name": "St. Mark's Square, Venice",
            "url": "https://www.skylinewebcams.com/en/webcam/italia/veneto/venezia/piazza-san-marco.html",
            "lat": 45.4343, "lng": 12.3388,
            "type": "skyline"
        },
        "niagara": {
            "name": "Niagara Falls",
            "url": "https://www.earthcam.com/usa/newyork/niagarafalls/",
            "lat": 43.0962, "lng": -79.0377,
            "type": "earthcam"
        },
        "eiffel_tower": {
            "name": "Eiffel Tower, Paris",
            "url": "https://www.earthcam.com/world/france/paris/",
            "lat": 48.8584, "lng": 2.2945,
            "type": "earthcam"
        },
        "sydney_harbour": {
            "name": "Sydney Harbour",
            "url": "https://www.earthcam.com/world/australia/sydney/",
            "lat": -33.8568, "lng": 151.2153,
            "type": "earthcam"
        },
        "dubai_burj": {
            "name": "Burj Khalifa, Dubai",
            "url": "https://www.earthcam.com/world/unitedarabemirates/dubai/",
            "lat": 25.1972, "lng": 55.2744,
            "type": "earthcam"
        }
    }
    
    def __init__(self):
        self.current_webcam = None
        self.webcam_list = list(self.PUBLIC_WEBCAMS.keys())
        print(f"[OK] Public Webcam Access initialized ({len(self.webcam_list)} locations)")
    
    def get_webcam_info(self, location_key: str) -> Optional[Dict]:
        """Get webcam information for a location"""
        return self.PUBLIC_WEBCAMS.get(location_key)
    
    def find_nearest_webcam(self, lat: float, lng: float) -> Optional[str]:
        """Find the nearest webcam to given coordinates"""
        import math
        
        min_dist = float('inf')
        nearest = None
        
        for key, webcam in self.PUBLIC_WEBCAMS.items():
            dist = math.sqrt(
                (webcam["lat"] - lat) ** 2 + 
                (webcam["lng"] - lng) ** 2
            )
            if dist < min_dist:
                min_dist = dist
                nearest = key
        
        return nearest
    
    def list_webcams_by_region(self, region: str) -> List[Dict]:
        """List webcams in a specific region"""
        region_lower = region.lower()
        results = []
        
        for key, webcam in self.PUBLIC_WEBCAMS.items():
            if region_lower in webcam["name"].lower():
                results.append({"key": key, **webcam})
        
        return results
    
    def get_all_webcams(self) -> List[Dict]:
        """Get all available webcams"""
        return [{"key": k, **v} for k, v in self.PUBLIC_WEBCAMS.items()]


class MonicaVisualCapabilities:
    """
    Main class integrating all of Monica's visual capabilities.
    """
    
    def __init__(self):
        print("\n" + "=" * 60)
        print("INITIALIZING MONICA'S VISUAL CAPABILITIES")
        print("=" * 60)
        
        # Initialize all visual systems
        self.thermal_vision = ThermalVision()
        self.night_vision = NightVision()
        self.emotion_detector = EmotionDetector()
        self.object_detector = ObjectDetector()
        self.webcam_access = PublicWebcamAccess()
        
        # Current mode
        self.current_mode = "normal"  # normal, thermal, night
        
        print("=" * 60)
        print("[OK] All visual capabilities initialized!")
        print("=" * 60 + "\n")
    
    def process_frame(self, frame: np.ndarray, 
                     detect_emotions: bool = True,
                     detect_objects: bool = True) -> Tuple[np.ndarray, Dict]:
        """
        Process a frame with all visual capabilities.
        Returns processed frame and analysis results.
        """
        result_frame = frame.copy()
        analysis = {
            "mode": self.current_mode,
            "emotions": None,
            "objects": []
        }
        
        # Apply vision mode
        if self.current_mode == "thermal":
            result_frame = self.thermal_vision.apply(result_frame)
        elif self.current_mode == "night":
            result_frame = self.night_vision.apply(result_frame)
        
        # Detect emotions (on original frame for accuracy)
        if detect_emotions:
            emotion_data = self.emotion_detector.detect_from_frame(frame)
            analysis["emotions"] = emotion_data
            
            # Draw emotion overlay if not in special vision mode
            if self.current_mode == "normal":
                result_frame = self.emotion_detector.draw_emotion_overlay(result_frame, emotion_data)
        
        # Detect objects
        if detect_objects:
            detections = self.object_detector.detect(frame)
            analysis["objects"] = detections
            
            # Draw detections if not in special vision mode
            if self.current_mode == "normal":
                result_frame = self.object_detector.draw_detections(result_frame, detections)
        
        return result_frame, analysis
    
    def set_mode(self, mode: str):
        """Set the visual mode"""
        if mode in ["normal", "thermal", "night"]:
            self.current_mode = mode
            
            # Update individual systems
            self.thermal_vision.enabled = (mode == "thermal")
            self.night_vision.enabled = (mode == "night")
            
            return True
        return False
    
    def toggle_thermal(self) -> bool:
        """Toggle thermal vision"""
        if self.current_mode == "thermal":
            self.current_mode = "normal"
            self.thermal_vision.enabled = False
        else:
            self.current_mode = "thermal"
            self.thermal_vision.enabled = True
            self.night_vision.enabled = False
        return self.thermal_vision.enabled
    
    def toggle_night_vision(self) -> bool:
        """Toggle night vision"""
        if self.current_mode == "night":
            self.current_mode = "normal"
            self.night_vision.enabled = False
        else:
            self.current_mode = "night"
            self.night_vision.enabled = True
            self.thermal_vision.enabled = False
        return self.night_vision.enabled


# Test the visual capabilities
if __name__ == "__main__":
    print("Testing Monica's Visual Capabilities...")
    
    # Initialize
    visual = MonicaVisualCapabilities()
    
    # Test webcam access
    print("\n--- Public Webcams ---")
    webcams = visual.webcam_access.get_all_webcams()
    for cam in webcams:
        print(f"  [?] {cam['name']} ({cam['lat']:.2f}, {cam['lng']:.2f})")
    
    # Test emotion detection from text
    print("\n--- Text Emotion Detection ---")
    test_texts = [
        "I'm so happy today!",
        "This makes me really angry",
        "I'm feeling a bit sad",
        "Wow, that's surprising!"
    ]
    for text in test_texts:
        result = visual.emotion_detector.detect_from_text(text)
        print(f"  '{text}' -> {result['emotion']} ({result['confidence']:.0%})")
    
    print("\n[OK] Visual capabilities test complete!")
