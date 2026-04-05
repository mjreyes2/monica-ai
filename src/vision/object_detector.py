"""
Monica AI - Universal Object Detection System

Uses YOLOv8 to detect ANY object in the camera frame:
- People, faces, hands, body parts
- Furniture (chairs, tables, desks, monitors)
- Room features (windows, doors, walls, picture frames)
- Personal items (phones, glasses, cups, books)
- Colors (skin tone, wall color, clothing color)
- 80+ COCO classes + custom color/scene analysis

All processing is LOCAL - no images sent to cloud.
"""

import cv2
import numpy as np
import time
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from collections import deque, Counter

logger = logging.getLogger("Monica.ObjectDetector")

# COCO 80 class names (YOLOv8 default)
COCO_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck",
    "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
    "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra",
    "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
    "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup",
    "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
    "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
    "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse",
    "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
    "refrigerator", "book", "clock", "vase", "scissors", "teddy bear",
    "hair drier", "toothbrush"
]

# Common color names mapped to HSV ranges
COLOR_RANGES = {
    "red":        ((0, 70, 50), (10, 255, 255)),
    "red2":       ((170, 70, 50), (180, 255, 255)),  # Red wraps around
    "orange":     ((10, 70, 50), (25, 255, 255)),
    "yellow":     ((25, 70, 50), (35, 255, 255)),
    "green":      ((35, 70, 50), (80, 255, 255)),
    "cyan":       ((80, 70, 50), (100, 255, 255)),
    "blue":       ((100, 70, 50), (130, 255, 255)),
    "purple":     ((130, 70, 50), (160, 255, 255)),
    "pink":       ((160, 70, 50), (170, 255, 255)),
}

# Skin tone categories (Fitzpatrick scale approximation in HSV)
SKIN_TONE_RANGES = {
    "very_light": ((0, 20, 180), (25, 120, 255)),
    "light":      ((0, 30, 150), (25, 150, 255)),
    "medium":     ((0, 40, 100), (25, 170, 230)),
    "olive":      ((0, 40, 80), (25, 160, 200)),
    "brown":      ((0, 50, 50), (25, 180, 180)),
    "dark":       ((0, 30, 30), (25, 180, 130)),
}


@dataclass
class DetectedObject:
    """A single detected object."""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    area: int
    color: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SceneAnalysis:
    """Full scene analysis result."""
    objects: List[DetectedObject]
    person_count: int
    dominant_colors: List[str]
    skin_tone: Optional[str]
    scene_description: str
    timestamp: float


class UniversalObjectDetector:
    """
    Detects any visible object using YOLOv8 + OpenCV color analysis.
    
    Capabilities:
    - 80 COCO object classes (person, chair, cup, book, phone, etc.)
    - Skin tone detection (Fitzpatrick scale)
    - Dominant color analysis (wall color, clothing, etc.)
    - Scene composition description
    - All LOCAL processing - zero cloud dependency
    """

    def __init__(self, model_path: str = None, confidence_threshold: float = 0.35):
        self.confidence_threshold = confidence_threshold
        self._model = None
        self._model_path = model_path
        self._yolo_available = False
        self._yolo_disabled_reason: Optional[str] = None
        self.last_result: Optional[SceneAnalysis] = None
        self.history = deque(maxlen=10)

        # Try to load YOLO
        self._init_yolo(model_path)

        # Fallback: OpenCV DNN + Haar cascades (always available)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def _init_yolo(self, model_path: str = None):
        """Initialize YOLOv8 model."""
        try:
            from ultralytics import YOLO

            project_root = Path(__file__).parent.parent.parent

            if model_path is None:
                # Auto-find model
                for name in ['yolov8s.pt', 'yolov8n.pt']:
                    p = project_root / 'models' / 'yolo' / name
                    if p.exists():
                        model_path = str(p)
                        break

            if model_path and Path(model_path).exists():
                self._model = YOLO(model_path)
                self._yolo_available = True
                logger.info(f"[OBJECTS] YOLOv8 loaded: {Path(model_path).name}")
                print(f"[OBJECTS] YOLOv8 loaded: {Path(model_path).name} (80 object classes)")
            else:
                # Auto-download yolov8n (6MB, fast for real-time)
                print("[OBJECTS] Downloading YOLOv8n model (first time only)...")
                self._model = YOLO('yolov8n.pt')
                self._yolo_available = True
                logger.info("[OBJECTS] YOLOv8n auto-downloaded and loaded")
                print("[OBJECTS] YOLOv8n loaded (80 object classes, real-time)")

            # Also load a custom-trained model if present
            custom_model_path = project_root / 'models' / 'yolo' / 'custom' / 'best.pt'
            if custom_model_path.exists():
                self._custom_model = YOLO(str(custom_model_path))
                n_classes = len(self._custom_model.names) if hasattr(self._custom_model, 'names') else '?'
                print(f"[OBJECTS] Custom YOLO model loaded: {n_classes} extra classes")
            else:
                self._custom_model = None

        except ImportError:
            logger.warning("[OBJECTS] ultralytics not installed - using OpenCV fallback")
            print("[OBJECTS] ultralytics not installed (pip install ultralytics)")
        except Exception as e:
            logger.warning(f"[OBJECTS] YOLO init error: {e}")
            print(f"[OBJECTS] YOLO init error: {e}")

    def detect(self, frame: np.ndarray) -> Optional[SceneAnalysis]:
        """
        Detect all objects in frame and analyze the scene.
        
        Returns SceneAnalysis with all detected objects, colors, and description.
        """
        if frame is None:
            return None

        try:
            objects = []

            # 1. YOLO object detection (80 classes)
            if self._yolo_available and self._model is not None:
                objects.extend(self._detect_yolo(frame))
            else:
                objects.extend(self._detect_fallback(frame))

            # 2. Color analysis
            dominant_colors = self._analyze_dominant_colors(frame)

            # 3. Skin tone detection (from face regions)
            skin_tone = self._detect_skin_tone(frame, objects)

            # 4. Add color info to detected objects
            for obj in objects:
                x1, y1, x2, y2 = obj.bbox
                roi = frame[max(0,y1):min(frame.shape[0],y2), 
                            max(0,x1):min(frame.shape[1],x2)]
                if roi.size > 0:
                    obj.color = self._get_dominant_color(roi)

            # 5. Build scene description
            person_count = sum(1 for o in objects if o.class_name == 'person')
            description = self._build_scene_description(objects, dominant_colors, skin_tone, person_count)

            result = SceneAnalysis(
                objects=objects,
                person_count=person_count,
                dominant_colors=dominant_colors,
                skin_tone=skin_tone,
                scene_description=description,
                timestamp=time.time()
            )

            self.last_result = result
            self.history.append(result)
            return result

        except Exception as e:
            logger.error(f"[OBJECTS] Detection error: {e}")
            return None

    def _detect_yolo(self, frame: np.ndarray) -> List[DetectedObject]:
        """Detect objects using YOLOv8."""
        objects = []
        try:
            results = self._model(frame, verbose=False, conf=self.confidence_threshold)

            for result in results:
                if result.boxes is None:
                    continue
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]

                    class_name = COCO_CLASSES[cls_id] if cls_id < len(COCO_CLASSES) else f"class_{cls_id}"
                    center = ((x1 + x2) // 2, (y1 + y2) // 2)
                    area = (x2 - x1) * (y2 - y1)

                    objects.append(DetectedObject(
                        class_name=class_name,
                        confidence=conf,
                        bbox=(x1, y1, x2, y2),
                        center=center,
                        area=area,
                    ))
        except Exception as e:
            err = str(e)
            # Common Windows/CUDA mismatch: torchvision::nms not available for CUDA.
            # Disable YOLO once and fall back to OpenCV detector to avoid per-frame
            # exception spam that can starve GUI/STT updates.
            if "torchvision::nms" in err and "CUDA" in err:
                self._yolo_available = False
                self._yolo_disabled_reason = "CUDA NMS backend unavailable"
                logger.warning(
                    "[OBJECTS] Disabling YOLO due to CUDA NMS backend error; using OpenCV fallback"
                )
            else:
                logger.error(f"[OBJECTS] YOLO detection error: {e}")

        # Also run custom model if available
        if getattr(self, '_custom_model', None) is not None:
            try:
                custom_results = self._custom_model(frame, verbose=False, conf=self.confidence_threshold)
                for result in custom_results:
                    if result.boxes is None:
                        continue
                    for box in result.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        x1, y1, x2, y2 = [int(v) for v in box.xyxy[0]]
                        class_name = self._custom_model.names.get(cls_id, f"custom_{cls_id}")
                        center = ((x1 + x2) // 2, (y1 + y2) // 2)
                        area = (x2 - x1) * (y2 - y1)
                        objects.append(DetectedObject(
                            class_name=class_name,
                            confidence=conf,
                            bbox=(x1, y1, x2, y2),
                            center=center,
                            area=area,
                        ))
            except Exception as ce:
                logger.debug(f"[OBJECTS] Custom model detection error: {ce}")

        return objects

    def _detect_fallback(self, frame: np.ndarray) -> List[DetectedObject]:
        """Fallback detection using OpenCV (faces + basic contour analysis)."""
        objects = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))
        for (x, y, w, h) in faces:
            objects.append(DetectedObject(
                class_name='person',
                confidence=0.6,
                bbox=(x, y, x+w, y+h),
                center=(x + w//2, y + h//2),
                area=w * h,
            ))

        return objects

    def _analyze_dominant_colors(self, frame: np.ndarray, top_n: int = 3) -> List[str]:
        """Analyze dominant colors in the frame using HSV histogram."""
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            color_counts = Counter()

            for name, (lower, upper) in COLOR_RANGES.items():
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                pixel_count = cv2.countNonZero(mask)
                if pixel_count > 500:  # Minimum threshold
                    # Merge red and red2
                    display_name = "red" if name == "red2" else name
                    color_counts[display_name] += pixel_count

            # Also detect white, gray, black, brown via value channel
            v_channel = hsv[:, :, 2]
            s_channel = hsv[:, :, 1]

            white_mask = (v_channel > 200) & (s_channel < 40)
            if np.sum(white_mask) > 1000:
                color_counts["white"] = int(np.sum(white_mask))

            black_mask = v_channel < 40
            if np.sum(black_mask) > 1000:
                color_counts["black"] = int(np.sum(black_mask))

            gray_mask = (v_channel > 40) & (v_channel < 200) & (s_channel < 40)
            if np.sum(gray_mask) > 1000:
                color_counts["gray"] = int(np.sum(gray_mask))

            # Sort by count and return top N
            top_colors = color_counts.most_common(top_n)
            return [c[0] for c in top_colors]

        except Exception:
            return []

    def _detect_skin_tone(self, frame: np.ndarray, objects: List[DetectedObject]) -> Optional[str]:
        """Detect skin tone from face regions."""
        try:
            # Find face regions from detected persons
            face_regions = []
            for obj in objects:
                if obj.class_name == 'person':
                    x1, y1, x2, y2 = obj.bbox
                    # Approximate face as top 1/3 of person bbox
                    face_h = (y2 - y1) // 3
                    face_regions.append(frame[y1:y1+face_h, x1:x2])

            # If no YOLO persons, try haar cascade
            if not face_regions:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))
                for (x, y, w, h) in faces:
                    face_regions.append(frame[y:y+h, x:x+w])

            if not face_regions:
                return None

            # Analyze the largest face region
            face_roi = max(face_regions, key=lambda r: r.size)
            if face_roi.size == 0:
                return None

            hsv_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
            best_tone = None
            best_count = 0

            for tone_name, (lower, upper) in SKIN_TONE_RANGES.items():
                mask = cv2.inRange(hsv_roi, np.array(lower), np.array(upper))
                count = cv2.countNonZero(mask)
                if count > best_count:
                    best_count = count
                    best_tone = tone_name

            return best_tone

        except Exception:
            return None

    def _get_dominant_color(self, roi: np.ndarray) -> Optional[str]:
        """Get the dominant color of a region."""
        if roi.size == 0:
            return None
        try:
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            best_color = None
            best_count = 0

            for name, (lower, upper) in COLOR_RANGES.items():
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                count = cv2.countNonZero(mask)
                display_name = "red" if name == "red2" else name
                if count > best_count:
                    best_count = count
                    best_color = display_name

            # Check neutrals
            v = hsv[:, :, 2]
            s = hsv[:, :, 1]
            white_count = int(np.sum((v > 200) & (s < 40)))
            black_count = int(np.sum(v < 40))
            gray_count = int(np.sum((v > 40) & (v < 200) & (s < 40)))

            for name, count in [("white", white_count), ("black", black_count), ("gray", gray_count)]:
                if count > best_count:
                    best_count = count
                    best_color = name

            return best_color
        except Exception:
            return None

    def _build_scene_description(self, objects: List[DetectedObject],
                                  colors: List[str], skin_tone: Optional[str],
                                  person_count: int) -> str:
        """Build a natural language scene description."""
        parts = []

        if person_count > 0:
            parts.append(f"{person_count} person(s) detected")
            if skin_tone:
                parts.append(f"skin tone: {skin_tone.replace('_', ' ')}")

        # Group objects by class
        obj_counts = Counter(o.class_name for o in objects if o.class_name != 'person')
        for name, count in obj_counts.most_common(10):
            if count == 1:
                parts.append(f"1 {name}")
            else:
                parts.append(f"{count} {name}s")

        if colors:
            parts.append(f"dominant colors: {', '.join(colors)}")

        return "; ".join(parts) if parts else "No objects detected"

    def get_object_list(self) -> List[str]:
        """Get simple list of currently detected object names."""
        if not self.last_result:
            return []
        return list(set(o.class_name for o in self.last_result.objects))

    def get_context_for_prompt(self) -> str:
        """Get scene context formatted for AI prompt injection."""
        if not self.last_result:
            return ""
        
        r = self.last_result
        lines = ["[VISION_CONTEXT]"]
        lines.append(f"Scene: {r.scene_description}")
        if r.skin_tone:
            lines.append(f"User skin tone: {r.skin_tone.replace('_', ' ')}")
        if r.objects:
            obj_list = ", ".join(f"{o.class_name}({o.confidence:.0%})" for o in r.objects[:15])
            lines.append(f"Objects: {obj_list}")
        lines.append("[/VISION_CONTEXT]")
        return "\n".join(lines)

    def get_status(self) -> Dict[str, Any]:
        """Get detector status."""
        return {
            'yolo_available': self._yolo_available,
            'model': self._model_path or 'none',
            'last_object_count': len(self.last_result.objects) if self.last_result else 0,
            'last_scene': self.last_result.scene_description if self.last_result else 'No data',
            'coco_classes': len(COCO_CLASSES),
        }


# Singleton
_detector = None

def get_object_detector() -> UniversalObjectDetector:
    """Get or create the object detector singleton."""
    global _detector
    if _detector is None:
        _detector = UniversalObjectDetector()
    return _detector
