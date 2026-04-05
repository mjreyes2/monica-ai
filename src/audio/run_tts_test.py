"""
Quick TTS sanity test for pronunciation and flow.

Usage:
  python -m monica_ai.src.tts.run_tts_test

It will synthesize two lines using the current TTS engine:
  1) Your DOB phrased naturally
  2) A 2025 question to verify year pronunciation

Notes:
  - If Piper voice models are not installed, it will fall back to system TTS.
  - Normalization (years, ordinals, dates) is applied before synthesis.
"""
from pathlib import Path
import time

try:
    from .tts_manager import TTSManager
    from .text_normalizer import normalize_text_for_tts
except Exception as e:
    print("Failed to import TTS modules:", e)
    raise


class _MinimalConfig:
    # Reasonable defaults; TTSManager will fall back if models are missing
    VOICES_DIR = Path("monica_ai/voices")
    DEFAULT_VOICE_MODEL = "en_US-amy-medium"  # Piper voice, optional
    TTS_SPEED = 1.0
    TTS_PITCH = 0.0
    TTS_ENGINE = "piper"  # try Piper, else fallback to system TTS


def speak_lines(tts: TTSManager, lines):
    for text in lines:
        print("\n[TTS-TEST] >", text)
        # Normalization is handled inside TTSManager, but keep explicit for visibility
        norm = normalize_text_for_tts(text)
        print("[TTS-TEST] Normalized:", norm)
        tts.speak(norm, block=True)
        time.sleep(0.2)


def main():
    config = _MinimalConfig()
    tts = TTSManager(config)

    # Configure anti-barge-in behavior (optional in this test)
    tts.enable_anti_barge_in = True
    tts.stop_on_user_speech = True
    tts.required_silence_ms = 300

    # Replace this with the confirmed DOB from the user (MM/DD/YYYY)
    user_dob = "04/20/1985"

    # Construct a natural reply using the date; the normalizer will fix ordinals/years
    dob_reply = "Your date of birth is April 20th, 1985."
    q_2025 = "What is the average income of an American in 2025?"

    speak_lines(tts, [dob_reply, q_2025])
    print("\n[TTS-TEST] Done.")


if __name__ == "__main__":
    main()
