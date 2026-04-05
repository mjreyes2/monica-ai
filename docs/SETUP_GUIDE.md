# Monica AI Advanced Modules - Quick Setup Guide

## ⚡ Quick Start (5 Minutes)

### Step 1: Verify Installation

Run the test suite to ensure all modules are working:

```bash
python test_monica_modules.py
```

Expected output:
```
✅ ALL TESTS PASSED!
```

### Step 2: Run the Demo

```bash
python demo_monica_advanced.py
```

This will:
- Create `monica_config.json` if it doesn't exist
- Open your camera
- Show real-time processing with overlays
- Press `s` for stats, `q` to quit

### Step 3: Configure Modules

Edit `monica_config.json` to enable/disable modules:

```json
{
  "night_vision": {"enabled": true},
  "emotion_fusion": {"enabled": false},  // Set true when models ready
  "presence_gauge": {"enabled": true}
}
```

## 🔧 Module-by-Module Setup

### 🌙 NightWatcher (Ready Out-of-Box)

**Status**: ✅ **Fully functional** (CPU-only, no model downloads needed)

**What it does**:
- Detects low-light conditions
- Applies CLAHE + gamma correction
- Routes enhanced frames when MediaPipe confidence drops

**No setup required!** Just enable in config:
```json
"night_vision": {"enabled": true}
```

### 👥 PresenceGauge (Ready Out-of-Box)

**Status**: ✅ **Fully functional** (uses OpenCV cascades)

**What it does**:
- Counts heads in frame
- Adjusts HUD scale based on crowd
- Increases activation thresholds for multi-person scenarios

**No setup required!** Just enable in config:
```json
"presence_gauge": {"enabled": true}
```

### 😊 EmotionFusion (Requires Model Setup)

**Status**: 🚧 **Needs model weights**

**Setup Instructions**:

1. **Navigate to emotion analyzer repo**:
   ```bash
   cd external/realtime-facial-emotion-analyzer
   ```

2. **Check if models exist**:
   ```bash
   ls models/
   ```

3. **If models missing, download**:
   - Check repo README for model download links
   - Typically need `weights.h5` and `shape_predictor_5_face_landmarks.dat`
   - Place in `external/realtime-facial-emotion-analyzer/models/`

4. **Install Python dependencies**:
   ```bash
   pip install tensorflow keras dlib opencv-python
   ```

5. **Enable in config**:
   ```json
   "emotion_fusion": {"enabled": true}
   ```

6. **Test**:
   ```bash
   cd external/realtime-facial-emotion-analyzer
   python video_main.py  # Should open camera and show emotions
   ```

## 📋 Integration Checklist

Use this to track your setup progress:

- [ ] Run `test_monica_modules.py` - all tests pass
- [ ] Run `demo_monica_advanced.py` - camera opens
- [ ] NightWatcher: Test in low-light (cover camera, watch for enhancement)
- [ ] PresenceGauge: Test with multiple people (should see count increase)
- [ ] EmotionFusion: Download models and test emotion detection
- [ ] Memory logs: Check `data/monica_memory.xlsx` for events
- [ ] ControlsSync: Run multiple windows, verify presence scale syncs

## 🎯 Common Use Cases

### Use Case 1: Stream with Multiple People

```python
from monica_ai import MonicaAI
from tracking_utils import ControlsSync

monica = MonicaAI()  # Auto-loads config
controls = ControlsSync()

# In your video loop:
face_event = monica.process_frame(frame)

# PresenceGauge auto-adjusts HUD
scale = controls.get_presence_scale()  # 0.5 when crowded
# Apply to your HUD elements
```

### Use Case 2: Night Streaming

```python
monica = MonicaAI()

# Enable NightWatcher
monica.config.night_vision.enabled = True
monica.config.night_vision.extra["low_light_threshold"] = 0.2

# Process frames
face_event = monica.process_frame(frame, mediapipe_confidence=0.6)
# If low light detected, enhanced frame used automatically
```

### Use Case 3: Emotion-Aware Interactions

```python
monica = MonicaAI()

# Get current emotion
if monica.emotion_fusion:
    fused = monica.emotion_fusion.get_fused_emotion()
    if fused and fused.primary_emotion == "happy":
        # Play upbeat sound
        sound = monica.get_sound("cheer")
        if sound:
            sound.play()
```

## 🐛 Troubleshooting

### Issue: "Import error" when running tests

**Solution**: Make sure all module files exist:
```bash
ls monica_config.py night_watcher.py emotion_fusion.py presence_gauge.py
```

### Issue: EmotionFusion not detecting emotions

**Cause**: Models not loaded

**Solution**:
1. Check `external/realtime-facial-emotion-analyzer/models/` exists
2. Download required model files (see EmotionFusion setup above)
3. Verify dependencies: `pip install tensorflow keras dlib`

### Issue: PresenceGauge detecting too many false positives

**Solution**: Increase confidence threshold in config:
```json
"presence_gauge": {
  "confidence_threshold": 0.8,  // Increase from 0.7
}
```

### Issue: Night vision activating too often

**Solution**: Lower low_light_threshold:
```json
"night_vision": {
  "extra": {
    "low_light_threshold": 0.10  // Lower = more strict
  }
}
```

## 📊 Performance Tuning

### If frame rate is low:

1. **Increase inference intervals** (process less frequently):
   ```json
   "night_vision": {"inference_interval": 1.0},      // Every 1 second
   "emotion_fusion": {"inference_interval": 3.0},    // Every 3 seconds
   "presence_gauge": {"inference_interval": 2.0}     // Every 2 seconds
   ```

2. **Disable heavy modules**:
   ```json
   "emotion_fusion": {"enabled": false}  // Most expensive
   ```

3. **Reduce batch size**:
   ```json
   "emotion_fusion": {"batch_size": 1}
   ```

### Target frame rates:

- **NightWatcher only**: 30+ FPS (very light)
- **NightWatcher + PresenceGauge**: 25+ FPS
- **All modules enabled**: 15-20 FPS (depends on hardware)

## 🚀 Next Steps

### Phase 1: Basic Usage (Current)
✅ Run tests  
✅ Run demo  
✅ Configure modules  

### Phase 2: Model Integration
🔲 Download EmotionFusion models  
🔲 Test emotion detection  
🔲 Fine-tune confidence thresholds  

### Phase 3: Advanced Integration
🔲 Wire up FCHD deep learning head detector  
🔲 Add vocal sentiment analysis  
🔲 Integrate psychology knowledge bases  

### Phase 4: Production
🔲 Optimize for real-time streaming  
🔲 Add GPU acceleration  
🔲 Create custom emotion models  

## 📚 Resources

- **Main Documentation**: `MONICA_ADVANCED_MODULES.md`
- **Test Suite**: `test_monica_modules.py`
- **Demo Application**: `demo_monica_advanced.py`
- **Configuration Reference**: See `monica_config.py` docstrings

## 💡 Pro Tips

1. **Start with minimal config**: Enable one module at a time
2. **Monitor stats**: Press `s` in demo to see performance metrics
3. **Check memory logs**: `data/monica_memory.xlsx` shows all events
4. **Tune for your camera**: Adjust thresholds based on lighting/environment
5. **Use presence awareness**: Let PresenceGauge auto-adjust your UI

---

**Questions or issues?** Check `MONICA_ADVANCED_MODULES.md` for detailed documentation.
