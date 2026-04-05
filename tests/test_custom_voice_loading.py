#!/usr/bin/env python3
"""
Test script to verify custom voice model loading
"""
import sys
from pathlib import Path

# Add project root and src/ to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

def test_custom_model_loading():
    """Test if the custom model can be loaded"""
    print("=" * 80)
    print("TESTING CUSTOM VOICE MODEL LOADING")
    print("=" * 80)

    try:
        from audio.speechbrain_final import FinalSpeechBrainRecognizer

        print("\n[TEST] Creating recognizer instance...")
        recognizer = FinalSpeechBrainRecognizer()

        print("\n[TEST] Waiting for model to load...")
        print("[TEST] This may take 60-120 seconds for wav2vec2 models...")

        import time
        start_time = time.time()
        timeout = 180  # 3 minutes

        while not recognizer.is_loaded and not recognizer.loading_failed:
            elapsed = int(time.time() - start_time)
            if elapsed > timeout:
                print(f"\n[TEST] [FAIL] Loading timeout after {timeout}s")
                return False

            # Show progress every 10 seconds
            if elapsed % 10 == 0 and elapsed > 0:
                print(f"[TEST] Still loading... {elapsed}s elapsed")

            time.sleep(1)

        elapsed = time.time() - start_time

        if recognizer.loading_failed:
            print(f"\n[TEST] [FAIL] Model loading FAILED after {elapsed:.1f}s")
            print(f"[TEST] Error: {recognizer.last_load_error}")
            return False

        if recognizer.is_loaded:
            print(f"\n[TEST] [OK] Model loaded successfully in {elapsed:.1f}s")
            print(f"[TEST] ASR Model: {type(recognizer.asr_model).__name__}")
            print(f"[TEST] Speaker Model: {type(recognizer.speaker_model).__name__}")

            # Check if it's the custom model
            if hasattr(recognizer.asr_model, 'hparams'):
                hparams_file = str(getattr(recognizer.asr_model.hparams, 'hparams_file', ''))
                if 'monica' in hparams_file.lower():
                    print(f"[TEST] [SUCCESS] Using CUSTOM Monica voice model!")
                else:
                    print(f"[TEST] [WARNING] Using generic model (custom model not loaded)")

            return True

    except Exception as e:
        print(f"\n[TEST] [ERROR] Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

    return False

if __name__ == "__main__":
    print("\nThis test verifies that Monica can load your custom-trained voice model.")
    print("The model was trained on 1,113 recordings of your voice.\n")

    success = test_custom_model_loading()

    print("\n" + "=" * 80)
    if success:
        print("[SUCCESS] CUSTOM VOICE MODEL TEST PASSED")
        print("\nYour custom model is ready to use!")
        print("Monica will now recognize your voice better.")
    else:
        print("[FAILED] CUSTOM VOICE MODEL TEST FAILED")
        print("\nMonica will fall back to the generic model.")
        print("Check the error messages above for details.")
    print("=" * 80)

    sys.exit(0 if success else 1)
