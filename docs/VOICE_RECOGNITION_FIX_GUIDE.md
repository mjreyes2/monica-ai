# Monica Voice Recognition Initialization Fix Guide

## Problem: "Voice Recognition Failed" Error

This guide addresses the common causes of voice recognition initialization failures in Monica AI.

## Common Causes & Solutions

### 1. Windows 11 Microphone Privacy Settings (MOST COMMON)

Windows 11 has stricter privacy controls that can block microphone access.

**Fix Steps:**
1. Press `Win + I` to open Windows Settings
2. Go to **Privacy & security** → **Microphone**
3. Ensure these are all **ON**:
   - "Microphone access" (system-wide)
   - "Let apps access your microphone"
   - **"Let desktop apps access your microphone"** ← CRITICAL!
4. Restart Monica AI

**Sources:**
- [Windows 11 Microphone Privacy Settings](https://www.headsetanswers.com/blogs/headset-answers/windows-11-microphone-privacy-settings)
- [Turn on app permissions for your microphone in Windows](https://support.microsoft.com/en-us/windows/turn-on-app-permissions-for-your-microphone-in-windows-94991183-f69d-b4cf-4679-c98ca45f577a)

### 2. PyAudio Device Detection Issues

**Check available audio devices:**
```bash
.venv\Scripts\python.exe -c "import pyaudio; p = pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]; p.terminate()"
```

**Fix:**
- Make sure your microphone is set as the **default input device** in Windows Sound Settings
- Right-click the speaker icon → **Sound settings** → **Input** → Select your microphone
- Check that it's not muted or disabled

**Sources:**
- [OSError: No Default Input Device Available](https://github.com/Uberi/speech_recognition/issues/414)
- [Anaconda's portaudio fails to detect default input device](https://github.com/ContinuumIO/anaconda-issues/issues/4139)

### 3. SpeechBrain Model Loading Failures

**CUDA Memory Errors:**
If you see "CUDA out of memory" or model loading failures:

```python
# The system should automatically fall back to CPU, but you can force it:
device = "cpu"  # Instead of "cuda"
```

**Model Download Issues:**
- SpeechBrain models download from HuggingFace on first run
- If download fails, delete the cache and retry:
  - Delete: `C:\Users\mxz\monica_project\models\speechbrain_personal\`
  - Restart Monica to re-download

**Sources:**
- [SpeechBrain CUDA out of memory error](https://speechbrain.discourse.group/t/speech-recognition-from-scratch-cuda-out-of-memory-error/192)
- [How to use GPU during inference](https://github.com/speechbrain/speechbrain/issues/574)

### 4. Python Environment Issues

**Reinstall speech recognition dependencies:**
```bash
cd C:\Users\mxz\monica_project
.venv\Scripts\python.exe -m pip install --upgrade --force-reinstall pyaudio sounddevice speechbrain torch torchaudio
```

**Sources:**
- [SpeechRecognition Library Guide](https://pypi.org/project/SpeechRecognition/)
- [Python Speech Recognition Troubleshooting](https://realpython.com/python-speech-recognition/)

### 5. Quick Diagnostic Test

Run this diagnostic script to identify the exact issue:

```bash
.venv\Scripts\python.exe -c "
import sys
print('=== Monica Voice Recognition Diagnostic ===\n')

# 1. Check PyAudio
try:
    import pyaudio
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    print(f'✅ PyAudio: OK ({device_count} devices found)')

    # List input devices
    print('\nAvailable Input Devices:')
    for i in range(device_count):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f'  [{i}] {info[\"name\"]}')
    p.terminate()
except Exception as e:
    print(f'❌ PyAudio FAILED: {e}')

# 2. Check SpeechBrain
try:
    import speechbrain
    print('\n✅ SpeechBrain: Installed')
except Exception as e:
    print(f'\n❌ SpeechBrain FAILED: {e}')

# 3. Check CUDA
try:
    import torch
    if torch.cuda.is_available():
        print(f'\n✅ CUDA: Available ({torch.cuda.get_device_name(0)})')
    else:
        print('\n⚠️  CUDA: Not available (will use CPU)')
except Exception as e:
    print(f'\n❌ Torch FAILED: {e}')

# 4. Check Microphone Access
try:
    import sounddevice as sd
    print('\n✅ SoundDevice: OK')
    print('\nTesting microphone access (5 seconds)...')
    recording = sd.rec(int(5 * 16000), samplerate=16000, channels=1, blocking=True)
    if recording.max() > 0.01:
        print('✅ Microphone: Working! (Audio detected)')
    else:
        print('⚠️  Microphone: No audio detected (check permissions or volume)')
except Exception as e:
    print(f'\n❌ Microphone access FAILED: {e}')
    print('\n🔧 Solution: Check Windows microphone permissions!')

print('\n=== Diagnostic Complete ===')
"
```

## Priority Fixes (Do These First)

1. **Enable Windows 11 microphone permissions** (Settings → Privacy & security → Microphone)
2. **Set microphone as default device** (Sound Settings → Input)
3. **Run the diagnostic test** above to identify specific failures
4. **Check the Monica console output** when it starts for specific error messages

## Still Having Issues?

If voice recognition still fails after trying these fixes:

1. **Check Monica's console output** for the specific error message
2. **Look for:**
   - `[AUDIO] Vosk initialization failed:`
   - `[FINAL-SPEECHBRAIN] Loading failed:`
   - `PyAudio error`
   - `CUDA error`
3. **Share the error message** for more specific help

## References

- [Speech Recognition Python: The Ultimate Guide (2025)](https://www.videosdk.live/developer-hub/stt/speech-recognition-python)
- [speechrecognition Guide: Complete Python Package Documentation](https://generalistprogrammer.com/tutorials/speechrecognition-python-package-guide)
- [Troubleshoot the Speech SDK - Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/troubleshooting)
- [Python Speech Recognition Tutorial](https://copyprogramming.com/howto/microphone-on-windows-not-working-for-speech-recognition-by-using-python)
