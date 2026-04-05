# Sci-Fi Sound Effects for AR/Holographic Teaching System

This directory contains futuristic sound effects for Monica's AR/Holographic teaching mode.

## Sound Categories

### Hologram Activation/Deactivation
- `hologram_activate.wav` - Hologram powers on
- `hologram_deactivate.wav` - Hologram powers off
- `hologram_appear.wav` - Object materializes
- `hologram_disappear.wav` - Object dematerializes

### Interface Sounds
- `interface_beep_01.wav` through `interface_beep_10.wav` - UI feedback
- `interface_click_01.wav` through `interface_click_05.wav` - Button clicks
- `interface_select.wav` - Menu selection
- `interface_confirm.wav` - Action confirmed
- `interface_error.wav` - Error notification

### Data Processing
- `data_processing_01.wav` through `data_processing_05.wav` - Computing sounds
- `data_transfer.wav` - Information flowing
- `data_complete.wav` - Process finished

### Step Navigation
- `step_next.wav` - Move to next step
- `step_previous.wav` - Move to previous step
- `step_complete.wav` - Step finished

### Ambient
- `ambient_hum.wav` - Background holographic hum
- `ambient_tech.wav` - Technology ambience

## Sources

Sound effects are from free, Creative Commons licensed sources:
- Freesound.org (CC0 and CC-BY licenses)
- Mixkit.co (Free for commercial use)
- Zapsplat.com (Free with attribution)

## Usage in Monica

```python
from monica_ai.src.ar_teaching.sound_manager import SoundManager

sound_mgr = SoundManager()
sound_mgr.play('hologram_activate')  # Play activation sound
sound_mgr.play('interface_beep_01')  # Play beep
```

## Manual Download Instructions

Since automated download requires API keys, download sounds manually:

1. **Freesound.org:**
   - Search: "hologram interface sci-fi"
   - Filter: CC0 license
   - Download 20-30 sounds

2. **Mixkit.co:**
   - Visit: https://mixkit.co/free-sound-effects/sci-fi/
   - Download interface and hologram sounds
   - No attribution required

3. **Zapsplat.com:**
   - Visit: https://www.zapsplat.com/sound-effect-category/science-fiction/
   - Download "Sci-Fi Console Beeps" pack (130 sounds)
   - Requires free account

Place all downloaded sounds in this directory.
