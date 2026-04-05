# Microphone Settings Guide for Monica AI

## Critical STT Fixes Applied

### 1. Audio Buffering Implemented ✅
- **Problem**: STT was processing tiny 64ms chunks - too short for the model to recognize speech
- **Solution**: Now accumulates 1.5 seconds of audio before processing
- **Result**: Model receives proper audio length for accurate transcription

### 2. Voice Activity Detection (VAD) Added ✅
- **Problem**: Processing silence and background noise continuously
- **Solution**: Only processes audio when level exceeds 0.02 threshold
- **Result**: Reduces false processing and improves accuracy

### 3. Smart Buffer Management ✅
- Waits for speech to finish (10 frames of silence) before processing
- Clears short buffers that don't contain enough speech
- Resets buffer when you stop listening

## Windows Microphone Settings

### Step 1: Open Sound Settings
1. Right-click the speaker icon in Windows taskbar (bottom right)
2. Select "Open Sound settings"
3. Click "Sound Control Panel" on the right side

### Step 2: Configure Your Microphone
1. Go to the "Recording" tab
2. Find your microphone device (the one Monica is using)
3. Right-click and select "Properties"

### Step 3: Adjust Levels
1. Go to the "Levels" tab
2. Set **Microphone volume to 80-100%**
3. If available, set **Microphone Boost to +10dB or +20dB**
4. Click "Apply"

### Step 4: Test Your Microphone
1. Go to the "Listen" tab (optional)
2. Check "Listen to this device" briefly to hear yourself
3. Speak at normal volume - you should hear yourself clearly
4. Uncheck "Listen to this device" when done

### Step 5: Advanced Settings (Optional)
1. Go to the "Advanced" tab
2. Set default format to **"1 channel, 16 bit, 16000 Hz (DVD Quality)"**
3. Uncheck "Allow applications to take exclusive control"
4. Click "Apply" and "OK"

## Testing Monica's Speech Recognition

### Expected Audio Levels:
- **Silence**: 0.00 - 0.02 (below VAD threshold)
- **Speaking**: 0.05 - 0.20 (triggers processing)
- **Loud speaking**: 0.20 - 0.50

### How to Test:
1. Launch Monica: `LAUNCH_MONICA.bat`
2. Click "Start Listening" button
3. **Wait 2-3 seconds**, then speak clearly: **"MONICA INITIALIZE"**
4. Watch the logs for:
   - `[VAD] Speech detected! Level: 0.15` (example)
   - `[STT-BUFFER] Processing 24000 samples (1.50s)`
   - `[STT-SUCCESS] Transcribed: 'monica initialize'`

### Troubleshooting:

**If you see lots of empty results:**
- Microphone volume is too low
- Follow Steps 1-3 above to increase volume

**If VAD never triggers (no "Speech detected" messages):**
- Your microphone boost is too low
- Try increasing boost to +20dB
- OR lower VAD threshold in code (change 0.02 to 0.01 in stt_service.py line 61)

**If Monica responds to background noise:**
- VAD threshold is too low
- Increase threshold to 0.03 or 0.04 in stt_service.py line 61

**If transcription is still inaccurate:**
- Speak more clearly and at normal volume
- Reduce background noise
- Make sure you're using the correct microphone device

## Settings Button Location

The Settings button is located in the **bottom right corner** of the Monica GUI window.

## Current Microphone Device

Based on your logs, Monica is using:
- **Device Index**: 1 (may vary between restarts)
- **Device Name**: Check logs for "Using audio device" message

To change the microphone device, use the Settings button in the GUI.
