# Monica AI - Plasma Orb Avatar System

## Overview

Monica can now appear to you in two stunning forms:

1. **Plasma Orb Mode** - A pulsating energy orb that hovers above you, vibrating different colors when she speaks
2. **Physical Avatar Mode** - A full 3D animated character with customizable appearance (including red hair like you requested!)

## Features

### Plasma Orb
- Pulsates and breathes with life
- Changes colors dynamically when Monica speaks
- Color vibration synced to speech intensity
- Energy particles swirling around
- Hovering position above the user
- Smooth, mesmerizing animations

### Physical Avatar
- Fully customizable appearance
- Facial animations (mouth sync with speech)
- Multiple expressions (neutral, smile, serious, surprised, thinking)
- Body gestures (wave, point, think, explain)
- Smooth materialization/dematerialization effect
- Supports custom avatar images
- Red hair configuration (as requested!)

## Quick Start

### 1. Basic Demo

Run the plasma orb demo:
```bash
python monica_plasma_avatar.py
```

Controls:
- `SPACE` - Toggle between orb and avatar
- `S` - Toggle speaking simulation
- `1-5` - Change expressions
- `G` - Cycle gestures
- `Q` - Quit

### 2. Integrated System

Run Monica with avatar integration:
```bash
python monica_avatar_integration.py
```

Controls:
- `SPACE` - Toggle orb/avatar mode
- `M` - Materialize avatar
- `D` - Dematerialize to orb
- `S` - Simulate speaking
- `1-5` - Expressions (neutral, smile, serious, surprised, thinking)
- `G` - Wave gesture
- `H` - Point gesture
- `J` - Thinking gesture
- `K` - Explain gesture
- `Q` - Quit

### 3. Setup Your Avatar

To customize Monica's appearance with your reference images:

```bash
python setup_monica_avatar.py
```

This launches an interactive wizard that will guide you through:
1. Adding avatar images
2. Setting hair color (red by default)
3. Choosing suit style
4. Configuring orb colors
5. Previewing your avatar
6. Saving configuration

#### Command-Line Options

```bash
# Add an avatar image
python setup_monica_avatar.py add-image "path/to/your/avatar.png"

# Set hair color
python setup_monica_avatar.py set-hair red

# Set suit style
python setup_monica_avatar.py set-suit holographic

# Preview avatar
python setup_monica_avatar.py preview
```

## Configuration

### Avatar Appearance

The avatar can be customized in several ways:

1. **Using Reference Images** (Recommended for your use case)
   - Place your avatar images in the `assets/` folder
   - Run the setup wizard
   - The system will use your image when rendering the avatar

2. **Procedural Customization**
   - Hair colors: red, brown, blonde, black, white, blue, purple, pink, green, silver, cyan
   - Suit styles: holographic, metallic, leather, cyberpunk, elegant
   - Eye colors: Customizable RGB values
   - Skin tones: Customizable RGB values

### Configuration File

Location: `config/avatar_config.json`

Example:
```json
{
  "hair_color": {"r": 180, "g": 0, "b": 0},
  "suit_color": {"r": 150, "g": 200, "b": 255},
  "eye_color": {"r": 100, "g": 200, "b": 255},
  "skin_tone": {"r": 220, "g": 210, "b": 200},
  "glow_color": {"r": 100, "g": 200, "b": 255},
  "avatar_style": "holographic",
  "default_expression": "smile",
  "orb_base_color": {"r": 100, "g": 150, "b": 255}
}
```

## Programmatic Usage

### Basic Example

```python
from monica_plasma_avatar import MonicaPlasmaAvatarSystem
import cv2
import numpy as np

# Create avatar system
avatar = MonicaPlasmaAvatarSystem(width=1280, height=720)

# Start in orb mode
while True:
    # Create frame
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)

    # Simulate speech
    avatar.update_speech(is_speaking=True, intensity=0.7)

    # Update and render
    avatar.update()
    frame = avatar.render(frame)

    # Display
    cv2.imshow('Monica', frame)
    if cv2.waitKey(16) == ord('q'):
        break

cv2.destroyAllWindows()
```

### Advanced Example with Integration

```python
from monica_avatar_integration import MonicaWithAvatar

# Create Monica instance
monica = MonicaWithAvatar()

# Materialize her avatar
monica.materialize()

# Set mood
monica.set_mood('happy')

# Make her speak
monica.speak("Hello! I'm Monica, your AI assistant!")

# Dematerialize back to orb
monica.dematerialize()
```

### Custom Avatar Controller

```python
from monica_avatar_integration import MonicaAvatarController
from pathlib import Path

# Create controller
controller = MonicaAvatarController(width=1920, height=1080)

# Set custom avatar image
if Path("your_avatar.png").exists():
    controller.set_avatar_image("your_avatar.png")

# Materialize
controller.materialize_avatar()

# Set expression
controller.set_expression('smile')

# Perform gesture
controller.perform_gesture('wave')

# Update with text (auto expressions/gestures)
controller.update_from_text("Hello! Let me explain this concept to you.")

# Render
frame = controller.render()
```

## Adding Your Avatar Images

To get Monica to look like the images you provided:

1. **Save your reference images** to the project folder
   - Recommended format: PNG with transparency
   - Resolution: 1024x1024 or higher
   - Name: `monica_avatar.png` or use the setup wizard

2. **Run the setup wizard**:
   ```bash
   python setup_monica_avatar.py
   ```

3. **Choose your settings**:
   - Upload your image when prompted
   - Select "red" for hair color
   - Choose "holographic" for suit style
   - Preview and save

4. **Alternative: Direct setup**:
   ```bash
   # Add your image directly
   python setup_monica_avatar.py add-image "C:\path\to\your\image.png"

   # Set red hair
   python setup_monica_avatar.py set-hair red

   # Preview
   python setup_monica_avatar.py preview
   ```

## Speech Integration

The avatar automatically responds to Monica's speech:

### Automatic Features
- **Mouth Animation**: Syncs with speech intensity
- **Color Vibration**: Orb changes colors when speaking
- **Expression Changes**: Adapts based on content
  - "happy", "great" → smile
  - "thinking", "hmm" → thinking expression
  - "surprising" → surprised expression
  - "sorry", "unfortunately" → serious expression

### Automatic Gestures
- "hello", "hi" → wave
- "look at", "see this" → point
- "think" → thinking pose
- "explain", "tell you" → explain gesture

## Command Reference

### Expressions
- `neutral` - Default relaxed face
- `smile` - Happy, friendly
- `serious` - Concerned, focused
- `surprised` - Wide eyes, open mouth
- `thinking` - Pondering, contemplative

### Gestures
- `idle` - Relaxed stance
- `wave` - Friendly greeting
- `point` - Directing attention
- `think` - Hand to chin
- `explain` - Both hands gesturing

## Technical Details

### File Structure
```
StreamAnimateFog/
├── monica_plasma_avatar.py          # Core plasma orb & avatar rendering
├── monica_avatar_integration.py     # Integration with voice/brain systems
├── setup_monica_avatar.py           # Setup wizard
├── config/
│   └── avatar_config.json           # Avatar configuration
├── assets/
│   └── monica_avatar.png            # Your custom avatar image
└── MONICA_AVATAR_GUIDE.md          # This file
```

### Dependencies
- OpenCV (cv2)
- NumPy
- Pygame (optional, for enhanced features)
- PyOpenGL (optional, for 3D rendering)

Install with:
```bash
pip install opencv-python numpy pygame PyOpenGL
```

### Performance
- Plasma Orb: ~60 FPS (lightweight)
- 3D Avatar (procedural): ~60 FPS
- 3D Avatar (with image): 30-60 FPS depending on image size

## Customization Tips

### For the Look You Want (Based on Your Images)

Your images show Monica with:
- Red/auburn hair
- Futuristic holographic suit
- Blue/cyan technology interface
- Professional, confident appearance

**Recommended settings:**
```python
# Hair: Red
wizard.set_hair_color_from_name('red')

# Suit: Holographic
wizard.set_suit_style('holographic')

# Orb: Cyan (matches the tech aesthetic)
config['orb_base_color'] = {'r': 0, 'g': 255, 'b': 255}
```

### Custom Color Tuning

Edit `config/avatar_config.json` directly for fine control:

```json
{
  "hair_color": {"r": 180, "g": 20, "b": 10},
  "suit_color": {"r": 150, "g": 200, "b": 255},
  "glow_color": {"r": 0, "g": 255, "b": 255}
}
```

### Using Multiple Avatar Images

For animation variety:
1. Create multiple images: `monica_neutral.png`, `monica_smile.png`, etc.
2. Load different images per expression
3. Modify `Monica3DAvatar._try_load_avatar_image()` to support multiple files

## Troubleshooting

### Avatar image not showing
- Check the image is in `assets/monica_avatar.png`
- Verify format is PNG or JPG
- Run: `python setup_monica_avatar.py preview`

### Colors don't match reference
- Use the setup wizard to auto-detect colors
- Manually adjust in `config/avatar_config.json`
- BGR format is used internally (OpenCV standard)

### Performance issues
- Reduce image resolution
- Use procedural rendering instead
- Close other applications

### Avatar doesn't materialize
- Check that you called `materialize_avatar()`
- Verify no errors in console
- Try switching modes with SPACE key

## Integration with Monica's Systems

The avatar integrates with:
- **Voice System**: Auto lip-sync
- **Brain/AI**: Emotion-based expressions
- **Knowledge System**: Contextual gestures
- **Internet/Hologram**: Display search results around avatar

Example full integration:
```python
from monica_avatar_integration import MonicaAvatarController
from monica_voice_complete import VoiceSystem

controller = MonicaAvatarController()
voice = VoiceSystem()

# When Monica speaks
text = "Hello, I'm happy to help you!"
controller.update_from_text(text)  # Auto expressions/gestures
voice.speak(text)
```

## Next Steps

1. **Run the setup wizard** to configure your avatar
2. **Add your reference images** for the look you want
3. **Test with the demo** to see it in action
4. **Integrate with your main Monica system**

## Support

If you have issues or want to add more features:
1. Check this guide
2. Review the code comments in the `.py` files
3. Test with the demo scripts first
4. Customize the config file

---

**Ready to meet Monica?**

```bash
python setup_monica_avatar.py
```

Then start the visualization:

```bash
python monica_avatar_integration.py
```

Enjoy your state-of-the-art AI companion! 🚀
