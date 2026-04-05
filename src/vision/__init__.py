"""Vision module for Monica AI - handles camera capture and processing"""
from .camera_manager import CameraManager

# Vision system with hand/face/gesture detection
try:
    from .vision_system import MonicaVisionSystem, VisionResult, get_vision_system
    HAS_VISION_SYSTEM = True
except ImportError:
    HAS_VISION_SYSTEM = False

__all__ = ['CameraManager', 'MonicaVisionSystem', 'VisionResult', 'get_vision_system']
