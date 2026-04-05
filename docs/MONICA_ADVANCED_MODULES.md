# Monica AI - Advanced Modules Integration

## 🚀 Overview

Monica has been enhanced with three powerful AI modules for improved perception, emotion awareness, and adaptive interaction:

- **🌙 NightWatcher**: Low-light vision enhancement
- **😊 EmotionFusion**: Multimodal emotion detection with temporal smoothing
- **👥 PresenceGauge**: Multi-person head detection and crowd awareness

## 📦 Architecture

### Core Components

```
monica_ai.py           # Enhanced MonicaAI class with module integration
monica_config.py       # Configuration system with per-module settings
night_watcher.py       # Low-light enhancement module
emotion_fusion.py      # Emotion detection and temporal fusion
presence_gauge.py      # Head counting and spatial analysis
tracking_utils.py      # Extended ControlsSync with presence awareness
```

### External Dependencies

The modules leverage these upstream repositories (in `external/`):

- **Low-Light Vision**: `DeepStack_ExDark`, `human`
- **Head Detection**: `FCHD-Fully-Convolutional-Head-Detector`, `head_detector`
- **Emotion Recognition**: `ResidualMaskingNetwork`, `Emotion-detection`, `realtime-facial-emotion-analyzer`, `Face_info`
- **Psychology/Cognitive**: `psychopy`, `jsPsych`, `lab.js`, `awesome-psychology`, `SoulChat`, `Awesome-LLM-in-Social-Science`

## 🎯 Module Details

### 🌙 NightWatcher

**Purpose**: Enhance video quality in low-light conditions and provide fallback when MediaPipe confidence drops.

**Features**:
- Automatic brightness detection
- CLAHE-based contrast enhancement
- Gamma correction for visibility boost
- Bilateral filtering for noise reduction
- Confidence-based frame routing

**Configuration**:
```json
"night_vision": {
  "enabled": true,
  "confidence_threshold": 0.3,
  "inference_interval": 0.5,
  "extra": {
    "low_light_threshold": 0.15
  }
}
```

**Usage**:
```python
monica = MonicaAI()
face_event = monica.process_frame(frame, mediapipe_confidence=0.4)
# If confidence < 0.3, NightWatcher's enhanced frame is used
```

### 😊 EmotionFusion

**Purpose**: Detect and track facial emotions with temporal smoothing for stable predictions.

**Features**:
- Multi-emotion detection (happy, sad, angry, fear, disgust, surprise, neutral)
- Temporal fusion across configurable window (default: 5 frames)
- Valence/Arousal mapping (circumplex model)
- Emotion tagging for memory logging
- Graceful fallback to basic face detection

**Configuration**:
```json
"emotion_fusion": {
  "enabled": true,
  "confidence_threshold": 0.6,
  "inference_interval": 2.0,
  "extra": {
    "emotions": ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"],
    "aggregate_window": 5
  }
}
```

**Usage**:
```python
monica = MonicaAI()
emotion_result = monica.emotion_fusion.process(frame)
if emotion_result:
    fused = monica.emotion_fusion.get_fused_emotion()
    tags = monica.emotion_fusion.get_emotion_tags()  # For memory logging
```

**Output Example**:
```python
FusedEmotion(
    primary_emotion='happy',
    confidence=0.87,
    emotion_distribution={'happy': 0.87, 'neutral': 0.13},
    valence=0.8,   # Positive
    arousal=0.7,   # High energy
    sample_count=5
)
```

### 👥 PresenceGauge

**Purpose**: Detect multiple people and adjust UI density/activation thresholds accordingly.

**Features**:
- Multi-face detection with NMS (Non-Maximum Suppression)
- Head counting with temporal averaging
- Crowd density calculation
- Spatial distribution analysis (centered, dispersed, left/right)
- Dynamic HUD scaling based on crowd
- Adaptive keyboard activation thresholds

**Configuration**:
```json
"presence_gauge": {
  "enabled": true,
  "confidence_threshold": 0.7,
  "inference_interval": 1.0,
  "extra": {
    "max_heads": 10,
    "nms_threshold": 0.3
  }
}
```

**Usage**:
```python
monica = MonicaAI()
presence_result = monica.presence_gauge.process(frame)

if presence_result:
    # Adjust HUD based on crowd
    should_adjust, scale = monica.presence_gauge.should_adjust_hud()
    if should_adjust:
        controls.update_presence_scale(scale)  # 0.5 = 50% size
    
    # Get adaptive activation threshold
    threshold = monica.presence_gauge.get_activation_threshold()
    # More people = higher threshold (0.5 → 0.9)
```

**Output Example**:
```python
PresenceResult(
    head_count=3,
    detections=[...],
    crowd_density=0.3,
    spatial_distribution='dispersed',
    processing_time=0.023
)
```

## 🔧 Configuration

### Creating Configuration

```python
from monica_config import MonicaConfig

config = MonicaConfig()
config.night_vision.enabled = True
config.emotion_fusion.enabled = True
config.presence_gauge.enabled = True
config.save()  # Saves to monica_config.json
```

### Configuration File Format

See `monica_config.json` (auto-generated on first run):

```json
{
  "debug_mode": false,
  "log_level": "INFO",
  "night_vision": {
    "enabled": true,
    "confidence_threshold": 0.3,
    "inference_interval": 0.5,
    "model_path": "external/DeepStack_ExDark",
    "extra": {"low_light_threshold": 0.15}
  },
  "emotion_fusion": {
    "enabled": false,
    "confidence_threshold": 0.6,
    "inference_interval": 2.0,
    "model_path": "external/realtime-facial-emotion-analyzer/models",
    "extra": {
      "emotions": ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"],
      "aggregate_window": 5
    }
  },
  "presence_gauge": {
    "enabled": true,
    "confidence_threshold": 0.7,
    "inference_interval": 1.0,
    "model_path": "external/FCHD-Fully-Convolutional-Head-Detector",
    "extra": {
      "max_heads": 10,
      "nms_threshold": 0.3
    }
  },
  "max_parallel_inferences": 2,
  "gpu_memory_fraction": 0.3,
  "use_cuda": false
}
```

## 🎬 Demo & Testing

### Quick Start

```bash
# Run the demo
python demo_monica_advanced.py
```

**Controls**:
- `q`: Quit
- `s`: Show comprehensive statistics

### Integration Example

```python
from monica_ai import MonicaAI
from tracking_utils import ControlsSync

# Initialize with auto-loaded config
monica = MonicaAI()
controls = ControlsSync()

# Process video frame
face_event = monica.process_frame(frame, mediapipe_confidence=0.75)

# Get module stats
stats = monica.get_all_stats()
print(stats)

# Access specific modules
if monica.presence_gauge:
    presence = monica.get_presence_stats()
    if presence["current_average"] > 2:
        print("Crowd detected!")
```

## 📊 Memory Integration

All modules log events to Monica's Excel memory store:

### Night Vision Events
```python
{
  "speaker": "night_watcher",
  "event": "low-light-enhance",
  "content": "Enhanced frame (brightness: 0.12)",
  "tags": ["vision", "enhancement"]
}
```

### Presence Events
```python
{
  "speaker": "presence_gauge",
  "event": "presence-update",
  "content": "3 people detected",
  "tags": ["presence", "crowd", "dispersed"],
  "extra": {
    "head_count": 3,
    "crowd_density": 0.3,
    "spatial": "dispersed"
  }
}
```

### Emotion Events
```python
{
  "speaker": "emotion_fusion",
  "event": "emotion-detect",
  "content": "Emotion: happy (0.87)",
  "tags": ["happy", "positive", "excited"],
  "extra": {
    "emotion": "happy",
    "confidence": 0.87,
    "valence": 0.8,
    "arousal": 0.7,
    "distribution": {"happy": 0.87, "neutral": 0.13}
  }
}
```

## 🔄 ControlsSync Integration

`ControlsSync` now supports presence-aware HUD scaling:

```python
controls = ControlsSync()

# Set presence scale (called by PresenceGauge automatically)
controls.update_presence_scale(0.7)  # 70% normal size

# Read presence scale in other windows
scale = controls.get_presence_scale()
# Apply to HUD elements: size = base_size * scale
```

## 🚧 Next Steps

### Phase 1: Environment Setup (Current)
- ✅ Module architecture created
- ✅ Configuration system implemented
- ✅ Integration with monica_ai.py
- ✅ ControlsSync extensions
- ✅ Demo script

### Phase 2: Model Integration (Next)
1. **Setup Python environments** for each external repo
   - Many require CUDA/PyTorch
   - Create isolated venvs or conda environments
   
2. **Test individual models**:
   ```bash
   # Example: Test emotion detection
   cd external/realtime-facial-emotion-analyzer
   python video_main.py
   ```

3. **Download model weights**:
   - ResidualMaskingNetwork: FER2013 weights
   - FCHD: VGG16-based head detector weights
   - Emotion-detection: Trained model files

4. **Wire up deep learning backends**:
   - Enable GPU acceleration (optional)
   - Load models in EmotionFusion lazy initializer
   - Test inference performance

### Phase 3: Cognitive Tooling
1. **Mine jsPsych/lab.js templates** for UI overlays
2. **Extract SoulChat prompts** for conversational enhancements
3. **Integrate awesome-psychology** knowledge for behavioral cues

## 🛠️ Development

### Adding New Modules

1. Create module file (e.g., `new_module.py`)
2. Add `ModuleConfig` to `monica_config.py`
3. Initialize in `MonicaAI.__init__`
4. Call in `MonicaAI.process_frame`
5. Add stats getter method

### Testing

```python
# Test individual module
from night_watcher import NightWatcher
from monica_config import ModuleConfig

config = ModuleConfig(enabled=True, confidence_threshold=0.3)
nw = NightWatcher(config)

result = nw.process(frame)
if result:
    cv2.imshow("Enhanced", result.enhanced_frame)
```

## 📝 Performance Notes

- **NightWatcher**: ~5-10ms per frame (CPU-only, fast)
- **EmotionFusion**: ~50-200ms per frame (depends on model, can be throttled)
- **PresenceGauge**: ~10-30ms per frame (OpenCV cascades, CPU-friendly)

Use `inference_interval` to throttle expensive operations:
- `0.5` = process every 0.5 seconds
- `2.0` = process every 2 seconds

## 📚 External Repos Reference

| Repository | Purpose | Integration Point |
|------------|---------|-------------------|
| `DeepStack_ExDark` | Low-light detection | NightWatcher (fallback, not yet wired) |
| `human` | Multi-modal detection (JS) | Future: Node.js bridge |
| `FCHD-Fully-Convolutional-Head-Detector` | Head detection | PresenceGauge (deep learning option) |
| `realtime-facial-emotion-analyzer` | Emotion detection | EmotionFusion (primary) |
| `ResidualMaskingNetwork` | FER emotion model | EmotionFusion (alternate) |
| `Emotion-detection` | Keras emotion model | EmotionFusion (alternate) |
| `psychopy` | Experiment framework | Future: Cognitive overlays |
| `jsPsych` | Web experiments | Future: In-window tasks |
| `lab.js` | Experiment builder | Future: Task templates |
| `awesome-psychology` | Knowledge base | Future: Prompt engineering |
| `SoulChat` / `SoulChat2.0` | Empathetic chatbot | Future: Conversational prompts |
| `Awesome-LLM-in-Social-Science` | LLM knowledge | Future: Context enrichment |

## 🎯 Goals Achieved

✅ **Modular architecture** - Each system is independently toggleable  
✅ **Configuration-driven** - JSON file for easy customization  
✅ **Performance-conscious** - Throttling, lazy loading, graceful degradation  
✅ **Memory integration** - All events logged with rich tags  
✅ **ControlsSync awareness** - Presence affects UI across windows  
✅ **Comprehensive stats** - Real-time monitoring of all modules  

## 📖 License

Inherits from parent project. External repositories have their own licenses (see respective repos).

---

**Ready to make Monica smarter! 🚀🤖**
