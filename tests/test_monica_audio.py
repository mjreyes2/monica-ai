"""
Test Monica's audio system to diagnose "Start Listening" issue.

This is a diagnostic script, not a pytest module.
Run directly: python tests/test_monica_audio.py
"""
import sys
from pathlib import Path

# Add project root and src/ to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))


def main():
    print("=" * 70)
    print("MONICA AUDIO SYSTEM DIAGNOSTIC")
    print("=" * 70)
    print()

    # Step 1: Check audio manager
    print("[1] Checking Audio Manager...")
    try:
        from audio.tts_manager import TTSManager as AudioManager
        from config.settings import AppConfig

        config = AppConfig()
        audio = AudioManager(config)
        print(f"   [OK] Audio Manager created")
        print(f"   - Input device: {audio.input_device_name}")
        print(f"   - Output device: {audio.output_device_name}")
        print()
    except Exception as e:
        print(f"   [ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Step 2: Check speech recognizer
    print("[2] Checking Speech Recognizer...")
    if hasattr(audio, 'speech_recognizer') and audio.speech_recognizer:
        recognizer = audio.speech_recognizer
        print(f"   [OK] Speech recognizer found: {type(recognizer).__name__}")

        has_register_callback = hasattr(recognizer, 'register_callback')
        has_start_listening = hasattr(recognizer, 'start_listening')
        has_callbacks_list = hasattr(recognizer, 'callbacks')

        print(f"   - Has register_callback(): {has_register_callback}")
        print(f"   - Has start_listening(): {has_start_listening}")
        print(f"   - Has callbacks list: {has_callbacks_list}")

        if has_callbacks_list:
            print(f"   - Callbacks registered: {len(recognizer.callbacks)}")
        print()
    else:
        print(f"   [ERROR] No speech recognizer found!")
        print(f"   - audio.speech_recognizer = {getattr(audio, 'speech_recognizer', None)}")
        print()

    # Step 3: Test callback registration
    print("[3] Testing Callback Registration...")
    callback_called = False
    recognized_text = None

    def _audio_callback(result):
        nonlocal callback_called, recognized_text
        callback_called = True
        if hasattr(result, 'text'):
            recognized_text = result.text
        elif isinstance(result, dict):
            recognized_text = result.get('text', str(result))
        elif isinstance(result, str):
            recognized_text = result
        else:
            recognized_text = str(result)
        print(f"\n   [OK] CALLBACK CALLED! Recognized: '{recognized_text}'")

    try:
        if hasattr(audio, 'speech_recognizer') and audio.speech_recognizer:
            audio.speech_recognizer.register_callback(_audio_callback)
            print(f"   [OK] Test callback registered")
            print(f"   - Total callbacks: {len(audio.speech_recognizer.callbacks)}")
        else:
            print(f"   [ERROR] Cannot register callback - no recognizer")
        print()
    except Exception as e:
        print(f"   [ERROR] registering callback: {e}")
        import traceback
        traceback.print_exc()
        print()

    # Step 4: Check if recognizer is loaded/ready
    print("[4] Checking Recognizer Status...")
    if hasattr(audio, 'speech_recognizer') and audio.speech_recognizer:
        recognizer = audio.speech_recognizer

        if hasattr(recognizer, 'recognizer'):
            inner_recognizer = recognizer.recognizer
            is_loaded = getattr(inner_recognizer, 'is_loaded', None)
            loading_failed = getattr(inner_recognizer, 'loading_failed', None)

            print(f"   - Loaded: {is_loaded}")
            print(f"   - Failed: {loading_failed}")

            if is_loaded == False and loading_failed == False:
                print(f"   [WAIT] Model is still loading... waiting...")
                import time
                start = time.time()
                while not is_loaded and not loading_failed and (time.time() - start) < 30:
                    time.sleep(1)
                    is_loaded = getattr(inner_recognizer, 'is_loaded', False)
                    loading_failed = getattr(inner_recognizer, 'loading_failed', False)
                    elapsed = int(time.time() - start)
                    if elapsed % 5 == 0:
                        print(f"      Waiting... {elapsed}s")

                print(f"   - Final status: loaded={is_loaded}, failed={loading_failed}")
        print()

    # Step 5: Test speech recognition
    print("[5] Testing Speech Recognition...")
    print("   Starting speech recognition...")
    try:
        success = audio.start_speech_recognition()
        print(f"   - start_speech_recognition() returned: {success}")

        if success:
            print()
            print("=" * 70)
            print("[SUCCESS] Speech recognition started successfully!")
            print("=" * 70)
            print()
            print("Please speak into your microphone...")
            print("Say 'Monica initialize' or 'test hello'")
            print()
            print("Listening for 15 seconds...")

            import time
            for i in range(15):
                time.sleep(1)
                if callback_called:
                    print(f"\n[SUCCESS] Callback was triggered.")
                    print(f"   Recognized: '{recognized_text}'")
                    break
                if i % 5 == 4:
                    print(f"   ... still waiting ({i+1}s)")

            if not callback_called:
                print()
                print("[ERROR] No callback was triggered after 15 seconds.")
                print()
                print("Possible issues:")
                print("  1. Microphone not capturing audio")
                print("  2. SpeechBrain model not recognizing speech")
                print("  3. Callback not being invoked")
                print()
                print("Let me check the audio input...")

                if hasattr(audio, 'get_audio_level'):
                    level = audio.get_audio_level()
                    print(f"  - Current audio level: {level:.4f}")
                    if level < 0.01:
                        print("  [WARNING] Audio level very low - check microphone!")

            audio.stop_speech_recognition()
        else:
            print(f"   [ERROR] Failed to start speech recognition")
            error = getattr(audio, 'last_start_error', None)
            if error:
                print(f"   Error: {error}")
        print()

    except Exception as e:
        print(f"   [ERROR] {e}")
        import traceback
        traceback.print_exc()
        print()

    print("=" * 70)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
