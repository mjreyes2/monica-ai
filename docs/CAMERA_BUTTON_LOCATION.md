# 📷 Camera Button Location Guide

## Where to Find the Camera Button

```
┌─────────────────────────────────────────────────────────────┐
│ Monica Holographic Keyboard                 ┌──────────────┐│
│                                             │  Camera 0    ││ ← HERE!
│                                             │ Click to     ││
│                                             │  change      ││
│                                             └──────────────┘│
│                                                             │
│                                                             │
│         [Your camera feed with holographic keyboard]       │
│                                                             │
│                                                             │
│                                                             │
│                                                             │
│                                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Location**: Top-right corner, 20 pixels from edges

**Appearance**:
- Blue background button
- Cyan (turquoise) border
- Shows current camera number
- "Click to change" hint text

---

## What Happens When You Click It

```
┌─────────────────────────────────────────────────────────────┐
│                  ╔═══════════════════════════════╗          │
│                  ║    Select Camera              ║          │
│                  ║ Current: Camera 0             ║          │
│                  ╠═══════════════════════════════╣          │
│                  ║                               ║          │
│                  ║  ┌─────────────────────────┐ ║          │
│                  ║  │  Camera 0  (Current)    │ ║          │
│                  ║  │  1920x1080 (Current)    │ ║          │
│                  ║  └─────────────────────────┘ ║          │
│                  ║                               ║          │
│                  ║  ┌─────────────────────────┐ ║          │
│                  ║  │  Camera 2               │ ║ ← Click to
│                  ║  │  1920x1080 (MSMF)       │ ║   switch!
│                  ║  └─────────────────────────┘ ║          │
│                  ║                               ║          │
│                  ║  ┌─────────────────────────┐ ║          │
│                  ║  │  Camera 4               │ ║          │
│                  ║  │  1280x720 (DirectShow)  │ ║          │
│                  ║  └─────────────────────────┘ ║          │
│                  ║                               ║          │
│                  ║ Click camera to switch        ║          │
│                  ║ Press ESC to cancel           ║          │
│                  ╚═══════════════════════════════╝          │
└─────────────────────────────────────────────────────────────┘
```

**Overlay Features**:
- Semi-transparent dark background
- Centered on screen
- Shows all available cameras
- Current camera highlighted in teal
- Each button shows resolution and backend
- Click any camera to switch
- Press ESC to cancel

---

## Step-by-Step Visual Guide

### Step 1: Find the Button
```
Look in top-right corner ──────────────┐
                                        │
                                        ▼
                            ┌──────────────┐
                            │  Camera 0    │
                            │ Click to     │
                            │  change      │
                            └──────────────┘
```

### Step 2: Click It
```
Click the button ─────────> [Click!]
                               │
                               ▼
                    Overlay appears!
```

### Step 3: Select Camera
```
                  ┌─────────────────────┐
                  │  Camera 0 (Current) │ ← Already using this
                  └─────────────────────┘

                  ┌─────────────────────┐
Click here ─────> │  Camera 2           │ ← Switch to this
                  └─────────────────────┘

                  ┌─────────────────────┐
Or here ────────> │  Camera 4           │ ← Or this
                  └─────────────────────┘
```

### Step 4: Camera Switches Instantly
```
Switching... ──> ✅ Camera changed!

Window continues running with new camera!
```

---

## Visual Comparison

### OLD WAY (Terminal Menu)
```
Terminal Window:
╔═══════════════════════════╗
║ MONICA - SELECT CAMERA    ║
║                           ║
║ [1] Camera 0              ║
║ [2] Camera 2              ║
║ [3] Camera 4              ║
║                           ║
║ Enter number:             ║
╚═══════════════════════════╝
         │
         ▼
    Type "2"
         │
         ▼
  Monica window opens
```

### NEW WAY (In-Window GUI) ✨
```
Monica Window:
╔═══════════════════════════╗
║ [Camera feed]  [Camera 0] ║ ← Button here!
║                           ║
║   [Holographic keyboard]  ║
║                           ║
╚═══════════════════════════╝
         │
         ▼
  Click button
         │
         ▼
  Overlay appears
         │
         ▼
  Click camera
         │
         ▼
 Instant switch! ✨
```

---

## Button States

### Normal State
```
┌──────────────┐
│  Camera 0    │  ← Blue background
│ Click to     │     Cyan border
│  change      │     White text
└──────────────┘
```

### Mouse Hover (Future Enhancement)
```
┌──────────────┐
│  Camera 0    │  ← Could glow brighter
│ Click to     │     when mouse hovers
│  change      │
└──────────────┘
```

### During Camera Selection
```
Button temporarily hidden while overlay is open
```

---

## Scrolling to Find Button

If window is small and button is off-screen:

```
Scroll up with mouse wheel ────────┐
                                    │
                                    ▼
                    ┌──────────────┐
                    │  Camera 0    │  ← Button appears!
                    │ Click to     │
                    │  change      │
                    └──────────────┘
```

---

## Size and Position

**Button Dimensions**:
- Width: 180 pixels
- Height: 50 pixels
- Padding from edge: 20 pixels

**Position**:
- Right: 20px from right edge
- Top: 20px from top edge
- Always visible (scrolls with content)

**Responsive**:
- Repositions when window resizes
- Always in top-right corner
- Scales with scroll offset

---

## Color Scheme

**Button Background**: RGB(30, 60, 120) - Deep space blue
**Button Border**: RGB(0, 255, 255) - Cyan glow
**Text**: RGB(255, 255, 255) - White
**Hint Text**: RGB(150, 150, 150) - Gray

Matches Monica's sci-fi holographic aesthetic! ✨

---

## Quick Reference

**Where**: Top-right corner
**What**: Camera selection button
**Click**: Opens overlay with all cameras
**Select**: Click any camera to switch
**Cancel**: Press ESC

**That's it!** 🎉

---

*Last updated: December 3, 2025*
