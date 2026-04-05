"""Comprehensive STT and TTS diagnostic script."""
import sys
import os

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.join(_script_dir, '..')
# src/ must come BEFORE monica_ai/src/ so that src/audio/tts_manager.py is found
sys.path.insert(0, os.path.join(_project_root, 'monica_ai', 'src'))
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, 'src'))
os.chdir(_project_root)

print("=" * 60)
print("MONICA AI - STT & TTS COMPREHENSIVE DIAGNOSTIC")
print("=" * 60)

# ========== STT ENGINES ==========
print("\n--- STT ENGINE CHECK ---")

# 1. Custom trained
print("\n1. Custom FinalSpeechBrainRecognizer:")
try:
    from audio.speechbrain_final import FinalSpeechBrainRecognizer
    print("   Import: OK")
    try:
        r = FinalSpeechBrainRecognizer()
        print("   Init: OK")
    except Exception as e:
        print(f"   Init FAILED: {e}")
except Exception as e:
    print(f"   Import FAILED: {e}")

# 2. SpeechBrain standard
print("\n2. SpeechBrain standard ASR:")
try:
    import speechbrain
    print(f"   speechbrain version: {speechbrain.__version__}")
    try:
        from speechbrain.inference.ASR import EncoderDecoderASR
        print("   EncoderDecoderASR import: OK")
    except ImportError:
        try:
            from speechbrain.inference.ASR import EncoderDecoderASR
            print("   EncoderDecoderASR import: OK")
        except ImportError as e:
            print(f"   EncoderDecoderASR import FAILED: {e}")
except ImportError as e:
    print(f"   speechbrain not installed: {e}")

# 3. Whisper
print("\n3. OpenAI Whisper:")
try:
    import whisper
    print(f"   Import: OK (version: {getattr(whisper, '__version__', 'unknown')})")
except ImportError:
    print("   NOT INSTALLED - pip install openai-whisper")

# 4. Vosk
print("\n4. Vosk offline STT:")
try:
    from vosk import Model as VoskModel
    print("   Import: OK")
    vosk_path = os.path.join("models", "vosk-model-small-en-us-0.15")
    if os.path.exists(vosk_path):
        print(f"   Model found: {vosk_path}")
    else:
        print(f"   Model NOT found at: {vosk_path}")
        # Check for any vosk model
        models_dir = os.path.join(_project_root, "models")
        if os.path.exists(models_dir):
            vosk_dirs = [d for d in os.listdir(models_dir) if 'vosk' in d.lower()]
            if vosk_dirs:
                print(f"   Found vosk dirs: {vosk_dirs}")
            else:
                print("   No vosk model directory found in models/")
except ImportError:
    print("   NOT INSTALLED - pip install vosk")

# 5. speech_recognition + PocketSphinx
print("\n5. speech_recognition + PocketSphinx:")
try:
    import speech_recognition as sr
    print(f"   speech_recognition: OK (v{sr.__version__})")
    r = sr.Recognizer()
    try:
        # Check if sphinx is available
        import pocketsphinx
        print("   PocketSphinx: OK")
    except ImportError:
        print("   PocketSphinx: NOT INSTALLED - pip install pocketsphinx")
except ImportError:
    print("   speech_recognition NOT INSTALLED - pip install SpeechRecognition")

# 6. PyAudio (needed for microphone)
print("\n6. PyAudio (microphone access):")
try:
    import pyaudio
    pa = pyaudio.PyAudio()
    device_count = pa.get_device_count()
    input_devices = []
    for i in range(device_count):
        info = pa.get_device_info_by_index(i)
        if info.get('maxInputChannels', 0) > 0:
            input_devices.append(f"  [{i}] {info['name']} ({int(info['defaultSampleRate'])}Hz)")
    pa.terminate()
    print(f"   Import: OK, {len(input_devices)} input devices:")
    for d in input_devices:
        print(f"   {d}")
except ImportError:
    print("   NOT INSTALLED - pip install pyaudio")
    print("   Alternative: pip install sounddevice")
except Exception as e:
    print(f"   ERROR: {e}")

# 7. sounddevice (alternative to PyAudio)
print("\n7. sounddevice (alternative mic access):")
try:
    import sounddevice as sd
    devices = sd.query_devices()
    inputs = [d for d in devices if d.get('max_input_channels', 0) > 0]
    print(f"   Import: OK, {len(inputs)} input devices")
except ImportError:
    print("   NOT INSTALLED")
except Exception as e:
    print(f"   ERROR: {e}")

# ========== TTS ENGINES ==========
print("\n\n--- TTS ENGINE CHECK ---")

# 1. Piper
print("\n1. Piper TTS:")
from pathlib import Path
piper_exe = Path(r"C:\Users\Marvi\AppData\Local\Temp\piper\piper\piper.exe")
print(f"   Executable: {'FOUND' if piper_exe.exists() else 'MISSING'} at {piper_exe}")

# Check voice models
voice_dirs = [
    Path("resources/voices"),
    Path("monica_ai/resources/voices"),
]
for vd in voice_dirs:
    if vd.exists():
        models = list(vd.rglob("*.onnx"))
        print(f"   {vd}: {len(models)} models")
        for m in models:
            size_mb = m.stat().st_size / (1024*1024)
            print(f"     - {m.name} ({size_mb:.1f} MB)")

# 2. Test Piper synthesis
print("\n2. Piper synthesis test:")
try:
    # Add src/ to path for config and audio modules
    _src_path = os.path.join(_project_root, 'src')
    if _src_path not in sys.path:
        sys.path.insert(0, _src_path)
    from config.settings import config
    from audio.tts_manager import TTSManager
    tm = TTSManager(config)
    print(f"   Engine: {tm.engine}, Initialized: {tm.is_initialized}")
    
    if tm.is_initialized:
        audio = tm._synthesize_piper("Hello, this is a test.")
        if audio is not None and len(audio) > 0:
            print(f"   Synthesis: OK ({len(audio)} samples, {len(audio)/tm.sample_rate:.1f}s)")
        else:
            print("   Synthesis: FAILED (no audio output)")
    else:
        print("   TTS not initialized!")
except Exception as e:
    print(f"   ERROR: {e}")

# 3. soundfile (needed for Piper output)
print("\n3. soundfile (audio I/O):")
try:
    import soundfile as sf
    print(f"   Import: OK (v{sf.__version__})")
except ImportError:
    print("   NOT INSTALLED - pip install soundfile")

# 4. pygame (audio playback)
print("\n4. pygame (audio playback):")
try:
    import pygame
    print(f"   Import: OK (v{pygame.version.ver})")
except ImportError:
    print("   NOT INSTALLED")

# 5. pyttsx3 (system TTS fallback)
print("\n5. pyttsx3 (system TTS fallback):")
try:
    import pyttsx3
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    print(f"   Import: OK, {len(voices)} voices available")
    for v in voices[:5]:
        print(f"     - {v.name}")
    engine.stop()
except Exception as e:
    print(f"   ERROR: {e}")

# ========== SUMMARY ==========
print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
