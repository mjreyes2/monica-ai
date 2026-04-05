"""Audio module for Monica AI - handles audio I/O and SpeechBrain speech recognition"""
from .audio_manager import AudioManager
from .wake_word import WakeWordDetector

__all__ = ['AudioManager', 'WakeWordDetector']
