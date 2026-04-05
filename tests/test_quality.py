#!/usr/bin/env python3
"""Test script to verify quality assessment works"""

import numpy as np
import sys
import os
sys.path.append(os.path.dirname(__file__))

from audio_quality_metrics import AudioQualityAssessment, QualityLevel

def create_test_audio(duration=2.0, sample_rate=16000, freq=440.0):
    """Create a simple test audio signal"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    # Create a sine wave with some noise
    signal = 0.5 * np.sin(2 * np.pi * freq * t)
    noise = 0.05 * np.random.randn(len(signal))
    audio = signal + noise

    return audio.astype(np.float32), sample_rate

def test_quality_assessment():
    """Test the quality assessment with a simple audio signal"""
    print("[TEST] Testing Quality Assessment...")

    # Create test audio
    audio, sr = create_test_audio()
    print(f"Created test audio: {len(audio)} samples at {sr}Hz")

    # Create quality assessor
    assessor = AudioQualityAssessment()

    # Test with a dummy phrase
    test_phrase = "hello world"

    try:
        # Assess quality
        result = assessor.assess_audio_quality_from_array(audio, sr, test_phrase)

        print("\n[CHART] Quality Assessment Results:")
        print(f"  Quality Level: {result.quality_level.value}")
        print(f"  MOS Score: {result.mos_score:.2f}")
        print(f"  SNR: {result.snr_db:.1f} dB")
        print(f"  THD: {result.thd_percent:.2f}%")
        print(f"  Voice Activity: {result.voice_activity_percent:.1f}%")
        print(f"  Background Noise: {result.background_noise.get('total_noise', 0):.1f}%")
        print(f"  Speech Clarity: {result.speech_clarity.get('clarity_score', 0):.1f}%")

        # Check if it passes
        passes = result.quality_level in [QualityLevel.GOOD, QualityLevel.FAIR]
        print(f"\n[OK] PASS: {passes}")

        if passes:
            print("[PARTY] Quality assessment is working! Recordings should pass.")
        else:
            print("[X] Quality assessment still failing - needs more work.")

        return passes

    except Exception as e:
        print(f"[X] Error in quality assessment: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_quality_assessment()
