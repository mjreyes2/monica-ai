"""Compatibility shim for FinalSpeechBrainRecognizer.

This module keeps legacy imports (`audio.speechbrain_final`) working by
re-exporting the implementation from `monica_ai.src.audio`.
"""

from monica_ai.src.audio.speechbrain_final import FinalSpeechBrainRecognizer

__all__ = ["FinalSpeechBrainRecognizer"]
