"""
Biometric Detection System for Monica AI.

Provides:
- Emotion detection (face + voice)
- Age estimation
- Identity recognition
- Heartbeat monitoring
"""

from .biometric_detector import (
    BiometricDetector,
    EmotionDetector,
    AgeDetector,
    IdentityRecognizer,
    HeartbeatDetector,
    EmotionResult,
    AgeResult,
    IdentityResult,
    HeartbeatResult,
)

__all__ = [
    'BiometricDetector',
    'EmotionDetector',
    'AgeDetector',
    'IdentityRecognizer',
    'HeartbeatDetector',
    'EmotionResult',
    'AgeResult',
    'IdentityResult',
    'HeartbeatResult',
]
