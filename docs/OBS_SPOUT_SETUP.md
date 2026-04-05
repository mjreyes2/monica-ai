# 📺 OBS Spout Setup Guide - Monica Keyboard

## ✅ What is Spout?

**Spout** allows you to send Monica's holographic keyboard directly into OBS without screen capture! This means:
- ✅ **No performance hit** - Direct GPU transfer
- ✅ **Perfect quality** - No compression
- ✅ **Transparent background** - Easy to overlay
- ✅ **Real-time** - Zero latency

**Spout Name**: `MonicaRoundHandKeyboard`

## 📥 Step 1: Install Spout Plugin for OBS

### Option A: Download Spout2 Plugin

1. **Download** the OBS Spout2 plugin:
   - Go to: https://github.com/Off-World-Live/obs-spout2-plugin/releases
   - Download latest `obs-spout2-plugin-x.x.x-windows.zip`

2. **Install**:
   - Extract the ZIP file
   - Copy `obs-spout2-plugin.dll` to your OBS plugins folder:
     - Usually: `C:\Program Files\obs-studio\obs-plugins\64bit\`
   - Restart OBS

### Option B: Use OBS Plugin Manager (if available)

1. Open OBS
2. Go to **Tools** → **Plugins**
3. Search for "Spout2"
4. Click Install

## 🎮 Step 2: Add Monica to OBS

### Add Spout Source:

1. **In OBS**, click the **+** button in Sources
2. Select **"Spout2 Capture"** (or just "Spout Capture")
3. Name it: `Monica Keyboard`
4. Click **OK**

### Configure Spout Source:

1. In the properties window:
   - **Spout Sender Name**: Select `MonicaRoundHandKeyboard` from dropdown
   - **Composite Mode**: Select "Premultiplied Alpha" (for transparency)
   - **Allow Transparency**: Check this box ✅

2. Click **OK**

## 🚀 Step 3: Test the Setup

### Start Monica:

1. Run: `.\run_monica_select_camera.bat`
2. Select your camera
3. Wait for Monica to load
4. You should see: `✅ Spout sender: MonicaRoundHandKeyboard`

### Check OBS:

1. Look at your OBS preview
2. You should see Monica's holographic keyboard!
3. The camera feed and effects should all be visible

### Position and Scale:

- **Right-click** the source in OBS
- Select **Transform** → **Edit Transform**
- Adjust position, scale, rotation as needed

## 🎨 Step 4: Make it Look Amazing

### Remove Background (Optional):

In Monica, press:
- **R** - Toggle green screen removal
- **B** - Toggle background blur

### Adjust Monica Settings:

- **+/-** - Brightness
- **[/]** - Contrast
- **;/'** - Saturation
- **,/.** - Sharpness

### OBS Filters (Optional):

Right-click source → **Filters** → Add:
- **Color Correction** - Fine-tune colors
- **Chroma Key** - Remove green if using green screen
- **Sharpen** - Enhance holographic effects

## 🐛 Troubleshooting

### "Spout2 Capture" not in OBS sources?

**Solution**: Spout plugin not installed
1. Download from: https://github.com/Off-World-Live/obs-spout2-plugin/releases
2. Install to OBS plugins folder
3. Restart OBS

### "MonicaRoundHandKeyboard" not in dropdown?

**Solution**: Monica not running
1. Make sure Monica is actually running
2. Check console for: `✅ Spout sender: MonicaRoundHandKeyboard`
3. If you see `⚠️ Spout not available`, SpoutGL is not installed

### Black screen in OBS?

**Solutions**:
1. **Check Composite Mode**: Set to "Premultiplied Alpha"
2. **Enable Transparency**: Make sure checkbox is ticked
3. **Restart both**: Close Monica and OBS, restart both

### Monica says "Spout not available"?

**Solution**: SpoutGL not installed in Python environment
```bash
.venv\Scripts\pip install SpoutGL
```

### Performance issues?

**Solutions**:
1. **Lower resolution**: Edit monica_round_hand_keyboard.py line 1550:
   ```python
   keyboard = RoundHandKeyboard(width=1280, height=720, camera_index=camera_index)
   ```

2. **Reduce effects**: In Monica:
   - Press **H** to hide hand skeleton
   - Press **D** to hide debug boxes
   - Lower video enhancements

3. **Check GPU usage**: Spout uses GPU, make sure it's not overloaded

## 💡 Pro Tips

### Layering in OBS:

Create multiple scenes with Monica:
1. **Scene 1**: Monica with camera feed (full view)
2. **Scene 2**: Monica keyboard only (hide camera, green screen mode)
3. **Scene 3**: Monica overlay (semi-transparent over gameplay)

### Transparency for Overlays:

1. In Monica: Press **R** for green screen
2. In OBS: Add **Chroma Key** filter to Monica source
3. Set key color to green (#00FF00)
4. Adjust similarity/smoothness
5. Now Monica floats over your content!

### Multiple Cameras:

Run multiple instances:
```bash
# Terminal 1
.venv\Scripts\python.exe monica_round_hand_keyboard.py 0

# Terminal 2
.venv\Scripts\python.exe monica_round_hand_keyboard.py 2
```

Each needs different Spout name (edit code to change).

### Hotkeys in OBS:

Set up hotkeys for:
- Show/Hide Monica source
- Switch between Monica scenes
- Toggle Monica filters

## 📋 Quick Reference

### Monica Keyboard Shortcuts:
- **F** - Fullscreen
- **M** - Maximize window
- **H** - Toggle hand skeleton
- **D** - Toggle debug boxes
- **R** - Green screen mode
- **ESC** - Exit

### Spout Info:
- **Sender Name**: `MonicaRoundHandKeyboard`
- **Resolution**: 1920x1080 (configurable)
- **Format**: RGBA (with alpha channel)
- **Frame Rate**: 60 FPS

### OBS Source Settings:
- **Type**: Spout2 Capture
- **Composite**: Premultiplied Alpha
- **Allow Transparency**: ✅ Yes

## 🎯 Complete Setup Checklist

- [ ] OBS Spout2 plugin installed
- [ ] OBS restarted after plugin install
- [ ] Monica running (`✅ Spout sender` in console)
- [ ] Spout2 Capture source added in OBS
- [ ] `MonicaRoundHandKeyboard` selected in dropdown
- [ ] Composite mode set to "Premultiplied Alpha"
- [ ] Monica visible in OBS preview
- [ ] Positioned and scaled as desired
- [ ] Effects and transparency configured

---

## 🎊 You're All Set!

Monica's holographic keyboard is now streaming into OBS via Spout!

**Start streaming with:** `.\run_monica_select_camera.bat`

Enjoy your sci-fi holographic keyboard overlay! 🚀✨
