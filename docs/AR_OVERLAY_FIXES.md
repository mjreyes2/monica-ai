# AR Overlay Fixes - Camera Feed Only
**Date:** December 14, 2025 12:35 PM

## Problem
When you said "show keyboard", "show dial", or "show globe", Monica was opening **separate windows** instead of rendering the AR overlays directly in the camera feed.

## Root Cause
The AR hologram system had dual rendering:
1. **Camera feed overlays** (correct) - rendered at `vision_system.py` line 949
2. **Separate green screen windows** (incorrect for your use case) - designed for OBS chroma key capture

The separate windows were being triggered by calls to:
- `self.keyboard_window.show()` 
- `self.dial_window.show()`
- `self.globe_window.show()`

## Changes Made

### File: `monica_ar_hologram_system.py`

#### 1. Keyboard (Lines 1086-1094)
**Before:**
```python
if self.show_holographic_keyboard:
    self._play_keyboard_appear_sound()
    # Also show the separate keyboard window (for OBS green screen)
    if self.keyboard_window:
        self.keyboard_window.show()
```

**After:**
```python
if self.show_holographic_keyboard:
    self._play_keyboard_appear_sound()
    # DISABLED: Separate window - render on camera feed only
    # if self.keyboard_window:
    #     self.keyboard_window.show()
```

#### 2. Dial (Lines 1405-1414)
**Before:**
```python
if self.show_holographic_dial:
    # Also show the separate dial window (for OBS green screen)
    if self.dial_window:
        self.dial_window.show()
```

**After:**
```python
if self.show_holographic_dial:
    # DISABLED: Separate window - render on camera feed only
    # if self.dial_window:
    #     self.dial_window.show()
```

#### 3. Globe Show (Lines 1789-1792)
**Before:**
```python
# Also show the separate globe window (for OBS green screen)
if self.globe_window:
    self.globe_window.set_location(user_lat, user_lng, user_name)
    self.globe_window.show()
```

**After:**
```python
# DISABLED: Separate window - render on camera feed only
# if self.globe_window:
#     self.globe_window.set_location(user_lat, user_lng, user_name)
#     self.globe_window.show()
```

#### 4. Globe Hide (Lines 1829-1831)
**Before:**
```python
# Also hide the separate globe window
if self.globe_window:
    self.globe_window.hide()
```

**After:**
```python
# DISABLED: Separate window - render on camera feed only
# if self.globe_window:
#     self.globe_window.hide()
```

## Result
Now when you say:
- **"Show keyboard"** → Keyboard appears IN camera feed
- **"Show dial"** → Dial appears IN camera feed  
- **"Show globe"** → Globe appears IN camera feed
- **"Show me [location]"** → Location marker appears IN camera feed

No more separate windows!

## Note: "Show Herself" (Orb)
The orb (Monica's visual presence) is intentionally designed as a **separate green screen window for OBS overlay**. According to the code comment at line 2595-2596:

> "Monica's orb is now in a separate green screen window for OBS overlay. No longer rendered on the main camera feed."

If you want the orb to also appear in the camera feed, that would require additional implementation work to add orb rendering to the camera overlay system.

## Verification Steps
1. **Restart Monica** (close completely and relaunch)
2. **Say "Monica initialize"** to activate her
3. **Test each command:**
   - "Show keyboard" → Should appear in camera preview
   - "Show dial" → Should appear in camera preview
   - "Show globe" → Should appear in camera preview
   - "Show me Orlando" → Should highlight Orlando in camera preview
4. **Confirm:** No separate windows should open

## If Issues Persist
If you still see separate windows after restart, let me know which specific command is causing it and I'll investigate further.
