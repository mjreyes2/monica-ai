# Camera Selection Guide

Your system has **3 cameras detected**:
- Camera 0
- Camera 2
- Camera 4

## Quick Start - Try Each Camera

Run these scripts to test each camera:

1. **[run_monica_cam0.bat](run_monica_cam0.bat)** - Test Camera 0
2. **[run_monica_cam2.bat](run_monica_cam2.bat)** - Test Camera 2
3. **[run_monica_cam4.bat](run_monica_cam4.bat)** - Test Camera 4

## Which Camera Should I Use?

Try each one and pick the camera that shows you! Usually:
- **Camera 0** = Built-in laptop webcam or first USB camera
- **Camera 2** = Second camera or virtual camera
- **Camera 4** = Third camera or specialized device

## What Got Fixed

✅ **Removed ALL debug text**:
- No more green "HANDS: X" text
- No more red "NO HANDS DETECTED" warning
- Clean, production-ready interface

✅ **Camera selection made easy**:
- Just run the batch file for your camera
- Or use: `python monica_round_hand_keyboard.py <camera_number>`

## Features

### Holographic Sci-Fi Effects ✨
- **Volumetric glow rings** - 15 animated rings when keys pressed
- **Energy particles** - Magenta particles burst on keypress
- **Energy rings** - Cyan expanding rings
- **Holographic grid** - Animated circular grid background
- **Scanlines** - Moving scanlines across keys
- **Energy flow** - Animated dots flowing between keys
- **Rotating borders** - Arc segments rotate when charging

### Color Palette 🎨
- **Cyan (0, 255, 255)** - Main hologram glow
- **Magenta (255, 0, 255)** - Particle effects
- **Neon Green (0, 255, 128)** - Hover state
- **Electric Yellow (255, 255, 0)** - Press highlights
- **Deep Space Blue (20, 40, 80)** - Key base color

### Hand Gestures 👋
- **Point** - Touch keys to type
- **Fist** - Grab and drag keyboard
- **Say "Monica"** - Activate voice assistant

### Keyboard Controls ⌨️
- **Arrow Keys** - Move keyboard position
- **Page Up/Down** - Scale keyboard size
- **Home** - Reset to default
- **ESC** - Quit

### Video Enhancements 🎥
- **R** - Toggle green screen
- **B** - Toggle background blur
- **+/-** - Brightness
- **[/]** - Contrast
- **;/'** - Saturation
- **,/.** - Sharpness
- **C** - Show settings

## Spout Output

The keyboard is broadcast as **"MonicaRoundHandKeyboard"** for OBS capture.

## Troubleshooting

**Camera shows wrong view?**
- Try a different camera number (0, 2, or 4)

**Hand detection not working?**
- Make sure you have good lighting
- Move closer/further from camera
- Clean camera lens
- Check camera permissions in Windows Settings

**Keyboard too small/large?**
- Press **Page Up** to make bigger
- Press **Page Down** to make smaller
- Press **Home** to reset

---

**Ready to start?** Run one of the camera scripts above! 🚀
