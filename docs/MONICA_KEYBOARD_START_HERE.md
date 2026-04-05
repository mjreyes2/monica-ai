# 🚀 MONICA HOLOGRAPHIC KEYBOARD - QUICK START

**Your sci-fi hand-tracking keyboard is ready!**

---

## ⚡ FASTEST START (1 Step)

Double-click this file:
```
run_monica_select_camera.bat
```

That's it! You'll see a camera selection menu, pick your camera, and Monica launches.

---

## 🎮 WHAT YOU GET

### ✨ Holographic Effects
- **Volumetric glow rings** - 15 layers of animated cyan rings on keypress
- **Particle system** - Magenta particles burst upward with physics
- **Energy rings** - Expanding cyan rings with fade
- **Holographic grid** - Animated circular platform
- **Scanlines** - Moving holographic scan patterns
- **Energy flow** - Glowing dots animate along connections
- **State-based colors** - Cyan/green/yellow/blue for different states

### 👋 Hand Tracking
- **Point with index finger** - Touch keys to type
- **Make a fist** - Grab and drag keyboard anywhere
- **Real-time detection** - MediaPipe hand tracking (21 landmarks)
- **Toggle visibility** - Show/hide hand skeleton and debug boxes

### 🎥 Camera Features
- **Camera selection menu** - Choose from all available cameras
- **Command-line selection** - Use specific camera index
- **Auto-detection** - Scans all camera backends

### 🖥️ Window Controls
- **Resizable window** - Drag corners to resize
- **Fullscreen mode** - Press F key
- **Maximize mode** - Press M key (borderless windowed)
- **Professional display** - 1920x1080 @ 60 FPS

### 📺 OBS Integration
- **Spout output** - Direct GPU frame sharing
- **Zero latency** - No performance hit
- **Transparent background** - Easy overlay
- **Perfect quality** - No compression

---

## 📋 ALL LAUNCH OPTIONS

### Option 1: Interactive Camera Selection (Recommended)
```bash
.\run_monica_select_camera.bat
```
Shows menu, you pick camera number.

### Option 2: Quick Launch with Specific Camera
```bash
.\run_monica_cam0.bat   # Camera 0
.\run_monica_cam2.bat   # Camera 2
.\run_monica_cam4.bat   # Camera 4
```

### Option 3: Command Line with Camera Number
```bash
.\run_monica.bat 0      # Use camera 0
.\run_monica.bat 2      # Use camera 2
```

### Option 4: Direct Python
```bash
.venv\Scripts\python.exe monica_round_hand_keyboard.py 2
```

---

## ⌨️ KEYBOARD CONTROLS

### Window Management
| Key | Function |
|-----|----------|
| **F** | Toggle fullscreen |
| **M** | Maximize window (borderless) |
| **ESC** | Quit application |

### Keyboard Position & Size
| Key | Function |
|-----|----------|
| **← → ↑ ↓** | Move keyboard position |
| **Page Up** | Scale larger |
| **Page Down** | Scale smaller |
| **Home** | Reset to default position/size |

### Display Toggles
| Key | Function | Default |
|-----|----------|---------|
| **H** | Toggle hand skeleton (cyan/magenta lines) | ON |
| **D** | Toggle debug boxes (green circles) | OFF |
| **R** | Toggle green screen removal | OFF |
| **B** | Toggle background blur | OFF |
| **C** | Show current settings | - |

### Video Enhancement
| Key | Function |
|-----|----------|
| **+ / -** | Adjust brightness |
| **[ / ]** | Adjust contrast |
| **; / '** | Adjust saturation |
| **< / >** (or **,** / **.** ) | Adjust sharpness |

---

## 🎨 HOLOGRAPHIC COLOR PALETTE

- **Cyan (0, 255, 255)** - Primary hologram glow, press effect
- **Magenta (255, 0, 255)** - Particle bursts, grab indicator
- **Neon Green (0, 255, 128)** - Hover highlights
- **Electric Yellow (255, 255, 0)** - Press accents
- **Deep Space Blue (20, 40, 80)** - Base key color
- **Dark Space (5, 5, 15)** - Background

---

## 🖐️ HAND GESTURES

### ☝️ Point (Index Finger Extended)
**Action**: Touch keys to type
**Visual Effect**:
- Cyan explosion effect
- Magenta particles spawn and float upward
- Energy rings expand from keypress
- Volumetric glow rings (15 layers)

### ✊ Fist / Closed Hand
**Action**: Grab and drag keyboard
**Visual Effect**:
- Magenta grab indicator appears at palm
- Move keyboard anywhere on screen
- Repositions entire keyboard

### 🗣️ Say "Monica" (Voice Control)
**Action**: Activate voice assistant
**Visual Effect**:
- Plasma orb appears at top
- Voice commands enabled
- Bioluminescent feedback

---

## 🎯 ROUND KEYBOARD LAYOUT

```
         1  2  3  4  5  6  7  8  9  0
              Q  W  U  I  O  P
            E R T Y   G H J K L
          A S D F       Z X C V B N M
              SPACE (center)
          ← BKSP DEL CLR
```

- **Center**: SPACE (100px)
- **Inner Ring**: E,R,T,Y,A,S,D,F (60px, 150px radius)
- **Middle Ring**: Q,W,U,I,O,P,G,H,J,K,L,Z,X,C,V,B,N,M (50px, 280px radius)
- **Outer Ring**: 1-0, BKSP, DEL, ←, CLR (48px, 420px radius)

---

## 📺 OBS SPOUT SETUP

**Complete guide**: [OBS_SPOUT_SETUP.md](OBS_SPOUT_SETUP.md)

### Quick Steps:

1. **Install Spout Plugin**
   - Download: https://github.com/Off-World-Live/obs-spout2-plugin/releases
   - Extract and copy to OBS plugins folder
   - Restart OBS

2. **Add Monica to OBS**
   - In OBS: Add Source → **Spout2 Capture**
   - Name it: `Monica Keyboard`
   - Spout Sender Name: `MonicaRoundHandKeyboard`
   - Composite Mode: **Premultiplied Alpha**
   - Allow Transparency: ✅

3. **Start Monica**
   - Run: `.\run_monica_select_camera.bat`
   - You should see: `✅ Spout sender: MonicaRoundHandKeyboard`
   - Monica appears in OBS!

---

## 🎬 PRODUCTION SETTINGS

For **streaming** or **clean recording**:

```
Press H → Turn off hand skeleton
Press D → Make sure debug boxes are off (default)
Press R → Enable green screen if needed
Press F → Go fullscreen
```

Result: Clean holographic keyboard, no debug elements, perfect for streaming!

For **testing** or **troubleshooting**:

```
Press H → Turn on hand skeleton (see tracking)
Press D → Turn on debug boxes (see detection)
Press C → Check all current settings
```

Result: Full visibility of what's being detected.

---

## 🔧 TECHNICAL DETAILS

### Dependencies (All in .venv)
- Python 3.10.11
- MediaPipe 0.10.21 - Hand tracking
- OpenCV 4.12.0 - Video capture
- pygame - Display and audio
- numpy - Math operations
- PIL - Image enhancements
- SpoutGL - OBS output

### Performance
- **Resolution**: 1920x1080
- **Frame Rate**: 60 FPS target
- **Hand Detection**: 0.5 confidence (balanced)
- **Tracking**: 0.5 confidence (balanced)
- **Model Complexity**: 1 (accurate)
- **Max Hands**: 2

### Spout Output
- **Sender Name**: `MonicaRoundHandKeyboard`
- **Format**: RGBA (with alpha channel)
- **Transfer**: Direct GPU (zero latency)

---

## 📖 DOCUMENTATION FILES

### Quick Guides
- **MONICA_KEYBOARD_START_HERE.md** ← You are here
- **CAMERA_SELECTION.md** - Camera setup guide
- **TOGGLE_CONTROLS.md** - H and D key toggles
- **OBS_SPOUT_SETUP.md** - Complete OBS integration guide

### Complete Feature Documentation
- **MONICA_HOLOGRAPHIC_KEYBOARD_FINAL.md** - All features, effects, controls
- **MONICA_FIXES_README.md** - What was fixed

---

## 🐛 TROUBLESHOOTING

### Wrong camera shows up?
**Solution**: Try different camera numbers
```bash
.\run_monica_cam0.bat
.\run_monica_cam2.bat
.\run_monica_cam4.bat
```
One of them will show you!

### Can't see hand skeleton?
**Solution 1**: Press **H** key to toggle it on

**Solution 2**: Check lighting
- Needs good visibility
- Move closer to camera
- Clean camera lens

**Solution 3**: Check console for hand detection messages

### Hand detection not working?
**Checklist**:
- [ ] Good lighting?
- [ ] Hands in camera view?
- [ ] Camera permissions enabled?
- [ ] Press D to see if green circles appear
- [ ] Try different distance from camera

### "MonicaRoundHandKeyboard" not in OBS dropdown?
**Solution 1**: Monica not running
- Make sure Monica is actually running
- Check console for: `✅ Spout sender: MonicaRoundHandKeyboard`

**Solution 2**: SpoutGL not installed
```bash
.venv\Scripts\pip install SpoutGL
```

**Solution 3**: Restart both
- Close Monica and OBS
- Restart both applications

### Black screen in OBS?
**Solution**:
1. Set Composite Mode: **Premultiplied Alpha**
2. Enable **Allow Transparency** checkbox
3. Restart both Monica and OBS

### Performance issues?
**Solution 1**: Lower resolution
Edit monica_round_hand_keyboard.py line 1550:
```python
keyboard = RoundHandKeyboard(width=1280, height=720, camera_index=camera_index)
```

**Solution 2**: Reduce effects
- Press H to hide hand skeleton
- Press D to ensure debug boxes off
- Lower video enhancements

**Solution 3**: Check GPU usage
- Spout uses GPU
- Make sure GPU not overloaded
- Close other GPU-heavy applications

### Keyboard too small?
**Solution**:
- Press **Page Up** multiple times
- Or grab with fist and reposition
- Press **Home** to reset

### Camera permission denied?
**Solution**:
1. Open Windows Settings
2. Privacy → Camera
3. Enable camera access for apps
4. Try launching Monica again

---

## 🎯 RECOMMENDED FIRST SESSION

### 1. Find Your Camera (1 minute)
```bash
.\run_monica_select_camera.bat
```
Pick the camera that shows you.

### 2. Test Hand Detection (2 minutes)
- Hold hand in front of camera
- See cyan/magenta skeleton appear
- Point with index finger
- Make a fist

### 3. Type Something (2 minutes)
- Point at SPACE key in center
- Touch it with fingertip
- Watch cyan explosion!
- Try typing your name

### 4. Customize Display (1 minute)
```
Press H → Toggle hand skeleton
Press D → Toggle debug boxes
Press F → Try fullscreen
Press M → Try maximize
```

### 5. Adjust Position (1 minute)
- Make a fist
- Drag keyboard around
- Or use arrow keys
- Page Up/Down to scale

### 6. Test in OBS (5 minutes)
Follow [OBS_SPOUT_SETUP.md](OBS_SPOUT_SETUP.md):
- Install Spout plugin
- Add Spout2 Capture source
- Select `MonicaRoundHandKeyboard`
- See Monica in OBS!

**Total time**: 10 minutes to experience everything!

---

## 💡 PRO TIPS

### Streaming Setup
1. Press **H** to hide hand skeleton (cleaner look)
2. Press **R** if using green screen
3. In OBS, add Chroma Key filter if needed
4. Position Monica as overlay on your content

### Multiple Cameras
Run multiple instances with different cameras:
```bash
# Terminal 1
.venv\Scripts\python.exe monica_round_hand_keyboard.py 0

# Terminal 2
.venv\Scripts\python.exe monica_round_hand_keyboard.py 2
```
(Requires editing code to change Spout sender name for each instance)

### Hotkeys in OBS
Set up OBS hotkeys for:
- Show/Hide Monica source
- Switch between Monica scenes
- Toggle Monica filters

### Layering in OBS
Create multiple scenes:
1. **Scene 1**: Monica with camera feed (full view)
2. **Scene 2**: Monica keyboard only (green screen mode)
3. **Scene 3**: Monica overlay (semi-transparent over gameplay)

---

## 📊 FEATURE COMPARISON

| Feature | Status | Notes |
|---------|--------|-------|
| Hand tracking | ✅ Working | MediaPipe 21-point detection |
| Holographic effects | ✅ Working | 15-layer volumetric rendering |
| Camera selection | ✅ Working | Interactive menu + command line |
| Window controls | ✅ Working | Fullscreen, maximize, resize |
| Display toggles | ✅ Working | H and D keys |
| OBS Spout | ✅ Working | GPU direct transfer |
| Video enhancements | ✅ Working | Brightness, contrast, etc. |
| Voice assistant | ✅ Working | Say "Monica" to activate |
| Particle physics | ✅ Working | Gravity simulation |
| Energy effects | ✅ Working | Rings, scanlines, flow |

---

## 🎉 YOU'RE ALL SET!

Monica's holographic keyboard is ready with:

✅ **Stunning visual effects** - Volumetric glows, particles, energy rings
✅ **Perfect hand tracking** - 21-point MediaPipe detection
✅ **Easy camera selection** - Interactive menu
✅ **Flexible window** - Fullscreen, maximize, resize
✅ **Clean toggles** - Show/hide debug elements
✅ **OBS integration** - Zero-latency Spout output
✅ **Production ready** - Professional quality visuals

**Start typing now:**
```bash
.\run_monica_select_camera.bat
```

Enjoy your state-of-the-art sci-fi holographic keyboard! 🚀✨

---

*Last updated: December 3, 2025*
*For technical details, see [MONICA_HOLOGRAPHIC_KEYBOARD_FINAL.md](MONICA_HOLOGRAPHIC_KEYBOARD_FINAL.md)*
*For OBS setup, see [OBS_SPOUT_SETUP.md](OBS_SPOUT_SETUP.md)*
