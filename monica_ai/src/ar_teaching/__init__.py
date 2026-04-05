"""
AR/Holographic Teaching System for Monica AI
Enables visual, step-by-step teaching with 3D animations and AR projections
"""

from .ar_teaching_coordinator import ARTeachingCoordinator, get_ar_coordinator
from .sound_manager import SoundManager

__all__ = ['ARTeachingCoordinator', 'get_ar_coordinator', 'SoundManager']
