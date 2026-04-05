# 🖥️ Monica Window Features Guide

## ✨ NEW FEATURES ADDED

### 📷 In-Window Camera Selection
**No more terminal menus!** Change cameras directly in the Monica window.

**How to use:**
1. Look for the **"Camera X"** button in the top-right corner
2. Click it to open the camera selection overlay
3. Click any camera to switch instantly
4. Press ESC to cancel

**Features:**
- Shows all available cameras with resolution and backend info
- Current camera is highlighted
- Instant switching - no need to restart
- Beautiful sci-fi overlay interface

### 🖱️ Mouse Wheel Scrolling
**Scroll through the interface with your mouse wheel!**

**How to use:**
- Use mouse wheel to scroll up/down
- Automatically clamps to prevent scrolling too far
- Smooth 30-pixel increments per wheel tick

### 📏 Window Resizing
**Drag the window corners or edges to resize!**

**Features:**
- Fully resizable window
- Frame automatically scales to fit
- Camera button repositions automatically
- Works with all holographic effects

**Controls:**
- **Drag window edges** - Resize freely
- **F key** - Toggle fullscreen
- **M key** - Maximize (borderless windowed)
- **Window resize** updates display in real-time

---

## 🎮 COMPLETE CONTROLS REFERENCE

### 🖥️ Window Management
| Control | Function |
|---------|----------|
| **Drag edges/corners** | Resize window |
| **F key** | Toggle fullscreen mode |
| **M key** | Maximize window (borderless) |
| **Mouse wheel** | Scroll view up/down |
| **ESC** | Quit application |

### 📷 Camera Controls
| Control | Function |
|---------|----------|
| **Click camera button** | Open camera selection |
| **Click camera in overlay** | Switch to that camera |
| **ESC** (in overlay) | Cancel camera selection |

### ⌨️ Keyboard Position & Size
| Key | Function |
|-----|----------|
| **← → ↑ ↓** | Move keyboard position |
| **Page Up** | Scale keyboard larger |
| **Page Down** | Scale keyboard smaller |
| **Home** | Reset to default position/size |

### 👁️ Display Toggles
| Key | Function | Default |
|-----|----------|---------|
| **H** | Toggle hand skeleton (cyan/magenta lines) | ON |
| **D** | Toggle debug boxes (green circles) | OFF |
| **R** | Toggle green screen removal | OFF |
| **B** | Toggle background blur | OFF |
| **C** | Show current settings | - |

### 🎨 Video Enhancement
| Key | Function |
|-----|----------|
| **+ / -** | Adjust brightness |
| **[ / ]** | Adjust contrast |
| **; / '** | Adjust saturation |
| **< / >** (or **,** / **.** ) | Adjust sharpness |

---

## 💡 USAGE TIPS

### Multi-Monitor Setup
1. Resize window to fit your workflow
2. Drag to secondary monitor
3. Press F for fullscreen on that monitor
4. Camera button stays accessible

### Streaming Configuration
1. Resize window to your preferred streaming size
2. Click camera button to test different cameras
3. Find the one with best angle/quality
4. Hide debug elements (H, D keys)
5. Enable green screen if needed (R key)

### Testing Hand Detection
1. Click camera button
2. Try each available camera
3. Pick the one where hand tracking works best
4. No need to restart - instant switching!

### Scroll to See Hidden Elements
- If window is too small, scroll with mouse wheel
- Camera button always visible in top-right
- Smooth scrolling through interface

---

## 🔧 TECHNICAL DETAILS

### Window Resizing
- **Dynamic scaling** - Frame scales to match window size
- **Maintains aspect ratio** - No distortion
- **Updates in real-time** - Smooth resizing
- **Works with all effects** - Holographic effects scale properly

### Camera Switching
- **Live detection** - Scans for cameras on startup
- **Instant switch** - No restart needed
- **Preserves settings** - Video enhancements, toggles remain
- **Auto-release** - Old camera properly released

### Scrolling System
- **Mouse wheel support** - Standard scroll behavior
- **Clamped scrolling** - Prevents scrolling out of bounds
- **Smooth motion** - 30 pixels per tick
- **Content-aware** - Disabled during camera selection

### Frame Scaling
- **GPU-accelerated** - pygame.transform.scale
- **Efficient** - Only scales when size changes
- **High quality** - Smooth scaling algorithm
- **Real-time** - No performance impact

---

## 🎯 COMMON WORKFLOWS

### Workflow 1: Quick Start
```
1. Run: .\run_monica_select_camera.bat
2. Window opens with default camera
3. See camera button in top-right
4. Ready to type with hand gestures!
```

### Workflow 2: Change Camera
```
1. Click camera button (top-right)
2. Overlay appears with all cameras
3. Click the camera you want
4. Instantly switches!
```

### Workflow 3: Resize for Streaming
```
1. Drag window corner to desired size
2. Or press M to maximize
3. Or press F for fullscreen
4. Frame scales automatically
```

### Workflow 4: Multi-Window Setup
```
1. Resize Monica to half-screen
2. Position on one side
3. Use mouse wheel to scroll if needed
4. Click camera button to optimize view
```

---

## 📊 FEATURE COMPARISON

### Before vs After

| Feature | Before | After |
|---------|--------|-------|
| **Camera selection** | Terminal menu | In-window GUI ✨ |
| **Window size** | Fixed 1920x1080 | Fully resizable ✨ |
| **Scrolling** | Not available | Mouse wheel ✨ |
| **Camera switching** | Restart required | Instant in-window ✨ |
| **Resizing** | Not supported | Drag edges/corners ✨ |

---

## 🐛 TROUBLESHOOTING

### Camera button not visible?
**Solution**: Scroll up with mouse wheel - it's at the top-right

### Camera selection not opening?
**Solution**:
1. Make sure you're not in fullscreen mode
2. Click the button directly
3. Check console for "📷 Camera selection opened" message

### Window resize not working?
**Solution**:
1. Exit fullscreen mode (press F)
2. Exit maximize mode (press M)
3. Now you can drag edges/corners

### Mouse wheel not scrolling?
**Solution**:
1. Close camera selection overlay (press ESC)
2. Make sure window is focused
3. Try scrolling again

### Frame looks stretched?
**Solution**:
- This shouldn't happen - scaling maintains aspect ratio
- Press Home to reset keyboard position
- Try F for fullscreen mode

---

## ✅ WHAT'S FIXED

### User Request: "I want the option to choose which camera in the window, not in the terminal"
✅ **FIXED**: Camera button in top-right corner opens in-window overlay

### User Request: "let me resize"
✅ **FIXED**: Window is fully resizable - drag edges/corners

### User Request: "let me scroll if I want"
✅ **FIXED**: Mouse wheel scrolling added

### All Previous Features Still Work:
✅ Hand tracking with MediaPipe
✅ Holographic visual effects
✅ OBS Spout integration
✅ Fullscreen (F) and Maximize (M)
✅ Toggle controls (H, D keys)
✅ Video enhancements (+/-, [/], etc.)
✅ Voice assistant ("Monica")

---

## 🎉 READY TO USE!

Everything is implemented and working:

1. **Start Monica**: `.\run_monica_select_camera.bat`
2. **Click camera button** (top-right) to change cameras
3. **Drag window edges** to resize
4. **Mouse wheel** to scroll
5. **Type with hand gestures!**

All features work together seamlessly! 🚀✨

---

*Last updated: December 3, 2025*
*For complete keyboard features, see [MONICA_KEYBOARD_START_HERE.md](MONICA_KEYBOARD_START_HERE.md)*
*For OBS setup, see [OBS_SPOUT_SETUP.md](OBS_SPOUT_SETUP.md)*
