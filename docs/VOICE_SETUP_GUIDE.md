# 🎤 MONICA CAN HEAR YOU NOW!

## ✅ What Just Happened

**Installed:**
- ✅ SpeechRecognition - Converts your voice to text
- ✅ PyAudio - Microphone input
- ✅ pyttsx3 - Text-to-speech (Monica talks back!)

**Created:**
- ✅ `monica_voice_listener.py` - Voice interface system
- ✅ `launch_monica_voice.py` - Quick launcher

---

## 🚀 How to Use Monica's Voice

### Quick Start:

```powershell
python launch_monica_voice.py
```

### What Happens:
1. Monica calibrates microphone for ambient noise
2. Starts listening continuously
3. Waits for wake word: **"Hey Monica"** or **"Monica"**
4. Processes your command
5. Speaks response back to you!

---

## 🗣️ Example Commands

### Basic Interaction:
- **"Hey Monica, hello"** → Monica greets you
- **"Monica, what time is it?"** → Tells you the time
- **"Monica, what's the date?"** → Tells you today's date
- **"Monica, how are you?"** → Status check

### Gaming:
- **"Monica, play game tic tac toe"** → Starts game
- **"Monica, start game chess"** → Starts chess
- **"Monica, play snake"** → Starts snake game

### Filters:
- **"Monica, put a magic hat on me"** → Applies magic hat filter
- **"Monica, give me sunglasses"** → Applies sunglasses
- **"Monica, add sparkles"** → Applies sparkle effect
- **"Monica, laser eyes"** → Applies laser eye effect

### Security:
- **"Monica, encrypt my files"** → Shows encryption status
- **"Monica, run security scan"** → Scans for threats
- **"Monica, check status"** → All systems status

### Knowledge:
- **"Monica, what is quantum computing?"** → Explains topic
- **"Monica, tell me about AES encryption"** → Educational response
- **"Monica, explain blockchain"** → Knowledge query

---

## 🎛️ Technical Details

### Wake Word Detection:
- Default wake word: **"monica"**
- Case-insensitive
- Can be customized

### Speech Recognition:
- **Online:** Google Speech Recognition (better accuracy)
- **Offline:** CMU Sphinx (fallback, no internet needed)
- **Future:** Can integrate Whisper for local processing

### Text-to-Speech:
- Uses Windows SAPI voices
- Automatically selects female voice if available
- Speaking rate: 175 words/minute
- Volume: 90%

### Microphone Setup:
- Auto-calibrates for ambient noise (2 seconds)
- Continuous listening mode
- Background thread processing
- Low CPU usage

---

## 🔧 Customization

### Change Wake Word:

Edit `launch_monica_voice.py`:
```python
monica_voice = MonicaVoiceInterface(
    use_wake_word=True, 
    wake_word="hey assistant"  # Change this
)
```

### Disable Wake Word (Always Listen):

```python
monica_voice = MonicaVoiceInterface(
    use_wake_word=False  # No wake word needed
)
```

### Adjust Voice Settings:

Edit `monica_voice_listener.py`:
```python
# In setup_voice() method:
self.tts_engine.setProperty('rate', 150)    # Slower
self.tts_engine.setProperty('volume', 1.0)  # Louder
```

---

## 🎮 Integration Options

### Option 1: Simple Demo
```powershell
python monica_voice_listener.py
```
Basic voice commands only

### Option 2: Full Monica Integration
```powershell
python launch_monica_voice.py
```
Complete Monica AI with voice

### Option 3: With Visuals
```powershell
# Terminal 1: Voice-activated Monica
python launch_monica_voice.py

# Terminal 2: Hologram display
python monica_hologram_scifi.py

# Terminal 3: Keyboard display
python monica_keyboard_round.py
```

---

## 🐛 Troubleshooting

### "No microphone detected"
- Check microphone is plugged in
- Check Windows privacy settings (Microphone access)
- Try: Settings → Privacy → Microphone → Allow apps

### "Could not understand audio"
- Speak clearly and at normal volume
- Reduce background noise
- Move microphone closer
- Check microphone levels in Windows

### "Speech recognition service unavailable"
- Check internet connection (for Google recognition)
- Or it will fallback to offline Sphinx
- Install Sphinx: `pip install pocketsphinx`

### Voice is too fast/slow
- Adjust rate in `setup_voice()` method
- Default: 175, Range: 50-300

### Wrong voice gender
- Windows uses available SAPI voices
- Install additional voices from Windows Store
- Or download Zira/David voices

---

## 📊 How It Works

```
Your Voice
    ↓
Microphone (PyAudio)
    ↓
Audio Buffer
    ↓
Speech Recognition (Google/Sphinx)
    ↓
Text: "Hey Monica, what time is it?"
    ↓
Wake Word Check ("monica" detected)
    ↓
Command: "what time is it?"
    ↓
Monica AI Processing
    ↓
Response: "The time is 3:45 PM"
    ↓
Text-to-Speech (pyttsx3)
    ↓
You hear Monica speak!
```

---

## 🎯 Voice Command Categories

| Category | Example | What Monica Does |
|----------|---------|------------------|
| **Greeting** | "Hello" | Greets you back |
| **Time/Date** | "What time is it?" | Tells time/date |
| **Gaming** | "Play tic tac toe" | Starts game |
| **Filters** | "Magic hat" | Applies AR filter |
| **Security** | "Run scan" | Security check |
| **Knowledge** | "What is..." | Answers question |
| **Encryption** | "Encrypt files" | Shows status |
| **Status** | "How are you?" | System status |

---

## 💡 Pro Tips

1. **Clear Speech:** Speak naturally, don't shout
2. **Wake Word First:** Say "Monica" then pause briefly
3. **Background Noise:** Works best in quiet room
4. **Internet:** Online recognition is more accurate
5. **Practice:** Monica learns your speech patterns
6. **Commands:** Be specific ("play game chess" not just "chess")

---

## 🔐 Privacy Note

**Your Voice Data:**
- Processed locally with pyttsx3
- Sent to Google for recognition (if online)
- Not stored or recorded by Monica
- Can use offline Sphinx for 100% privacy

**To Use Fully Offline:**
1. Install: `pip install pocketsphinx`
2. Disable Google recognition in code
3. All processing stays on your PC

---

## 🎊 Summary

✅ **Monica can now:**
- Hear your voice through microphone
- Recognize what you say
- Respond with voice
- Execute commands
- Control all features hands-free!

**Commands to remember:**
- Wake word: **"Hey Monica"** or **"Monica"**
- Be specific with commands
- Wait for her response
- Say "goodbye" to exit

---

## 🚀 Quick Start Commands

```powershell
# Start voice-activated Monica
python launch_monica_voice.py

# Then say:
"Hey Monica, hello"
"Monica, what time is it?"
"Monica, play game tic tac toe"
"Monica, put a magic hat on me"
"Monica, run security scan"
"Monica, what is encryption?"
```

**Monica is now listening!** 🎤✨
