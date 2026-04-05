# Fix for "Start Listening" Issue

**Date**: 2025-12-12
**Issue**: Monica doesn't respond when you click "Start Listening"

---

## What I Fixed

I added better debug logging to the speech recognition callback system to identify the exact problem. The logs will now show:

1. Whether the speech recognizer is available
2. Whether the callback is successfully registered
3. How many callbacks are registered
4. Audio capture status (every ~6 seconds)
5. When speech is detected and recognized

---

## How to Test

### Step 1: Run Monica

```batch
RUN_MONICA.bat
```

### Step 2: Check Console for Callback Registration

Look for these messages in the console:

```
[GUI] Registering speech callback with SpeechBrain
[GUI] Speech recognizer type: <class 'monica_ai.src.audio.speechbrain_final.FinalMonicaAudio'>
[GUI] Has register_callback: True
[GUI] [OK] SpeechBrain speech callback registered! Total callbacks: 1
```

**If you see "Total callbacks: 1"** - callback is registered correctly ✓

**If you see "No speech recognizer available"** - there's an initialization issue ✗

### Step 3: Click "Start Listening"

Click the "[Mic] Start Listening" button.

**Expected messages:**
```
[GUI] _toggle_listening called! is_listening=False
[GUI] Checking speech engine: google_stt=False
[GUI] Calling audio.start_speech_recognition()...
[AUDIO] start_speech_recognition() called
[AUDIO] Calling SpeechBrain start_listening()...
[FINAL-MONICA] Started listening! Status: Ready
[FINAL-MONICA] Audio stream opened - listening for speech...
[FINAL-MONICA] Voice threshold: 0.01, callbacks: 1
```

**Key things to check:**
- `callbacks: 1` - means your callback is registered ✓
- `Voice threshold: 0.01` - means speech detection sensitivity
- `Audio stream opened` - means microphone is working ✓

### Step 4: Speak into Microphone

Say clearly: **"Monica initialize"** or **"test hello"**

**Watch for these messages:**

**Every ~6 seconds you should see:**
```
[FINAL-MONICA] Audio level: 0.0234, speaking: true, buffer: 15234 samples
```

- `Audio level` should be > 0.01 when you speak (if < 0.01, mic not picking up audio)
- `speaking: true` means voice activity detected
- `buffer: N samples` means audio is being captured

**When you stop speaking (after ~1.5s silence):**
```
[FINAL-MONICA] Recognized: 'monica initialize'
[GUI] _on_speech_recognized called with result type: <class 'str'>
[GUI] Extracted text: 'monica initialize', is_final: True
[GUI] Scheduling processing of: 'monica initialize'
[SPEECH] Processing: 'monica initialize'
[SPEECH] *** MONICA INITIALIZE DETECTED *** in: 'monica initialize'
```

**Then Monica should speak!**

---

## Troubleshooting

### Problem 1: No callbacks registered

**Symptoms:**
```
[WARNING] [GUI] No speech recognizer available for callback registration!
```

**Solution:**
- The speech recognizer didn't initialize properly
- Check earlier in the console for errors related to SpeechBrain
- Look for "[AUDIO] [OK] SpeechBrain FinalMonicaAudio ready!"

### Problem 2: Audio level always near 0.0000

**Symptoms:**
```
[FINAL-MONICA] Audio level: 0.0001, speaking: false, buffer: 0 samples
```
Even when you're speaking loudly.

**Solution:**
- Microphone not working or wrong mic selected
- Check Windows Sound Settings → Input → Make sure correct microphone is selected and not muted
- Try speaking VERY loudly to see if level increases

### Problem 3: Speech detected but not recognized

**Symptoms:**
```
[FINAL-MONICA] Audio level: 0.0523, speaking: true, buffer: 23456 samples
```
But no "Recognized:" message appears after you stop speaking.

**Solutions:**
- **Speech too short:** Speak for at least 1 second
- **Model still loading:** Wait 30 seconds after startup for SpeechBrain to load
  - Look for: "[FINAL-SPEECHBRAIN] All models loaded successfully"
- **Noisy environment:** Try in a quieter location

### Problem 4: Recognized but callback not called

**Symptoms:**
```
[FINAL-MONICA] Recognized: 'test hello'
```
But no "[GUI] _on_speech_recognized called" message.

**Solution:**
- This is a callback registration bug
- The callback was NOT properly registered
- **Send me the full console output** and I'll investigate

### Problem 5: Callback called but Monica doesn't respond

**Symptoms:**
```
[GUI] _on_speech_recognized called
[SPEECH] Processing: 'monica initialize'
```
But Monica doesn't speak or show response in GUI.

**Solution:**
- TTS (text-to-speech) issue
- Check if TTS is initialized: Look for "[INIT] TTS Manager ready!"
- Try typing a message instead and clicking Send to see if text responses work

---

## What to Send Me

If Monica still doesn't respond, please send me:

1. **Full console output** from startup until you finish speaking
2. **Screenshot** of the main window
3. **Tell me:**
   - Did you see "Total callbacks: 1"?
   - What was the audio level when you spoke?
   - Did you see "Recognized: ..." message?
   - Did you see "_on_speech_recognized called"?

---

## Expected Fix Timeline

Based on the debug output, I can:
- Identify if it's a callback, microphone, recognition, or TTS issue
- Provide a targeted fix within minutes
- Test the fix with you immediately

---

**Last Updated**: 2025-12-12
**Status**: Debug logging added, ready for testing
