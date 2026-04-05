# 🔥 Monica Ultimate - Quick Start Guide

## What's New?

Monica has been **completely transformed** with:

✅ **Natural AI Voice** - Soft, sensual, intelligent (Coqui TTS/Google TTS)  
✅ **AR Background Effects** - Voice-controlled sparkles, vortex, stars, matrix, etc.  
✅ **Hands-Free Mode** - Just say "Monica" to activate  
✅ **Advanced Brain** - Understands complex questions, remembers everything  
✅ **Knowledge Bases** - Health (GERD), fitness, cooking, relationships  
✅ **Grammar Teaching** - Corrects and explains grammar  
✅ **Memory Database** - SQLite stores all conversations forever  

## Launch Monica

```powershell
cd C:\Users\mxz\StreamAnimateFog
python launch_monica_ultimate.py
```

That's it! Monica will:
1. Load the best available voice engine
2. Start listening for wake word "Monica"
3. Enable AR effects controller
4. Wait for you to talk

## Basic Usage

### Activate Monica

Just say one of these:
- **"Monica"**
- **"Hey Monica"**
- **"OK Monica"**

Then ask your question!

### Example Conversations

**You:** "Monica, how are you?"  
**Monica:** "I'm doing great! How can I help you today?"

**You:** "Monica, tell me about GERD."  
**Monica:** "GERD is gastroesophageal reflux disease. Foods to avoid include spicy foods, citrus, chocolate, and caffeine..."

**You:** "Monica, recommend a workout."  
**Monica:** "For beginners, I recommend starting with bodyweight exercises like squats, push-ups, and lunges..."

**You:** "Monica, give me a recipe."  
**Monica:** "Here's a GERD-safe recipe: Oatmeal Breakfast Bowl. Start with 1 cup of oats..."

### AR Effects

**You:** "Monica, add sparkles"  
**Monica:** "Adding sparkles to the environment!" ✨  
*Screen fills with glitter*

**You:** "Monica, create a vortex"  
**Monica:** "Opening a vortex!" 🌀  
*Background swirls into portal*

**You:** "Monica, change background to stars"  
**Monica:** "Adding starfield!" ⭐  
*Space background appears*

**You:** "Monica, stop effects"  
**Monica:** "Removing effects!"  
*Back to normal*

## Available AR Effects

Say "Monica, [effect name]":

- **"add sparkles"** - Glitter particles
- **"add particles"** - Magic particle system
- **"add waves"** - Wave distortion
- **"create vortex"** - Portal swirl
- **"add glow"** - Ethereal aura
- **"change background to gradient"** - Color gradient
- **"add stars"** - Starfield
- **"enter the matrix"** - Matrix falling code
- **"create nebula"** - Cosmic cloud
- **"activate cyber grid"** - Cyberpunk wireframe
- **"stop effects"** - Remove all effects

## Keyboard Controls (Optional)

- **SPACE** - Manual listen (if continuous mode off)
- **C** - Toggle continuous listening
- **V** - Toggle your visibility
- **D** - Toggle object detection
- **G/B/K/T** - Background colors
- **Q** - Quit

## Voice Quality

Monica automatically selects the best voice engine:

1. **Coqui TTS** (if espeak-ng installed) - ⭐⭐⭐⭐⭐ BEST
2. **Google TTS** (if online) - ⭐⭐⭐⭐ GOOD
3. **pyttsx3** (always works) - ⭐⭐ BASIC

### Get the BEST Voice Quality

**Install espeak-ng** for Coqui TTS (natural AI voice):

1. Download from: https://github.com/espeak-ng/espeak-ng/releases
2. Run `espeak-ng-X64.msi` installer
3. Add `C:\Program Files\eSpeak NG` to PATH
4. Restart terminal

Or with Chocolatey:
```powershell
choco install espeak-ng -y
```

See `ESPEAK_NG_INSTALL.md` for detailed instructions.

## Test Voice Engines

```powershell
python test_monica_voice.py
```

This tests all available engines so you can hear the difference!

## Test AR Effects

```powershell
python monica_ar_controller.py
```

Opens test window - press 'N' to cycle through effects.

## Troubleshooting

### Monica doesn't respond

- Check microphone permissions
- Say "Monica" clearly
- Wait for blue status indicator
- Try keyboard: press SPACE to manually trigger

### No voice / silent

- Check speakers/volume
- Verify voice engine loaded (look for "✅ Advanced voice engine loaded")
- Test with: `python test_monica_voice.py`

### Robotic voice

- Install espeak-ng for Coqui TTS (see above)
- Without it, Monica uses Google TTS (still good) or pyttsx3 (basic)

### AR effects not working

- Say full command: "Monica, add sparkles" (not just "sparkles")
- Check AR controller loaded: "✅ AR controller ready"
- Try simpler effects first (glow, sparkles)

### Performance issues

- Press V to disable background removal
- Use simpler AR effects
- Close other applications
- Check CUDA is active (GPU should be used)

## OBS Integration

Monica outputs to **Spout: "MonicaUltimate"**

In OBS:
1. Add Source → Spout2 Capture
2. Select "MonicaUltimate"
3. Monica appears with AR effects!

Perfect for livestreaming! 🎥

## Features Summary

### What Monica Can Do

**Conversation:**
- Natural human-like voice
- Remembers all interactions
- Context-aware responses
- Emotion-based speech

**Knowledge:**
- Health: GERD foods, herbs, remedies
- Fitness: Workouts, proper form, equipment
- Cooking: GERD-safe recipes
- Relationships: Dating, intimacy advice
- Grammar: Teaching and corrections

**Visuals:**
- Background removal (GPU-accelerated)
- AR effects (10+ types)
- Flame visualization
- Object detection

**Modes:**
- Hands-free: Always listening for wake word
- Manual: Press SPACE to activate
- Continuous conversation: Context memory

## Files

**Launch:** `launch_monica_ultimate.py`  
**Test Voice:** `test_monica_voice.py`  
**Test AR:** `monica_ar_controller.py`  
**Memory:** `monica_memory.db` (SQLite database)

**Documentation:**
- `MONICA_NATURAL_VOICE_GUIDE.md` - Voice & AR complete guide
- `COMPLETE_TRANSFORMATION_SUMMARY.md` - Technical details
- `ESPEAK_NG_INSTALL.md` - Voice quality upgrade
- `MONICA_ULTIMATE_GUIDE.md` - Full feature guide

## Next Steps

1. **Launch:** `python launch_monica_ultimate.py`
2. **Say:** "Monica, hello!"
3. **Try AR:** "Monica, add sparkles"
4. **Ask questions:** Health, fitness, cooking, anything!
5. **Enjoy livestreaming** with natural AI voice and AR effects!

## Need Help?

Check documentation files:
- Voice issues → `ESPEAK_NG_INSTALL.md`
- AR effects → `MONICA_NATURAL_VOICE_GUIDE.md`
- Full features → `COMPLETE_TRANSFORMATION_SUMMARY.md`

## What's Better Than Before?

| Feature | Before | After |
|---------|--------|-------|
| Voice | ❌ Robotic Zira | ✅ Natural AI (Coqui/gTTS) |
| Conversation | ❌ Stilted, repetitive | ✅ Fluid, contextual |
| Interaction | ❌ Keyboard required | ✅ Hands-free voice |
| Memory | ❌ None | ✅ SQLite database |
| Knowledge | ❌ Limited | ✅ Health/fitness/cooking/etc |
| Background | ❌ Static | ✅ AR effects (voice controlled) |
| Teaching | ❌ None | ✅ Grammar corrections |
| Understanding | ❌ Basic | ✅ Advanced NLU + LLM |

**Monica is now a fully autonomous, intelligent, natural-sounding AI assistant!** 🔥✨

Enjoy! 🎤🎨🧠💾
