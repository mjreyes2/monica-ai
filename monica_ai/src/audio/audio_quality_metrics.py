#!/usr/bin/env python3
"""
Compatibility wrapper for Audio Quality Metrics

This file now delegates to the robust, lightweight implementation at
monica_ai.voice_training.quality_shim to avoid prior syntax issues.
It preserves the original public API names used by the recorder.
"""

from monica_ai.voice_training.quality_shim import (
    AudioQualityMetrics,
    AudioQualityAssessment,
    QualityLevel,
)

__all__ = [
    "AudioQualityMetrics",
    "AudioQualityAssessment",
    "QualityLevel",
]
