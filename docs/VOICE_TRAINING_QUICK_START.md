# Voice Training Quick Start Guide

## How to Use the Voice Training GUI

### Method 1: Double-Click Batch File (Easiest)
```
Double-click: START_VOICE_TRAINING.bat
```

### Method 2: Python Command
```bash
.venv\Scripts\python.exe launch_voice_training_gui.py
```

### Method 3: Direct Module
```bash
.venv\Scripts\python.exe monica_ai\voice_training\record_voice.py
```

## GUI Features

### 1. Recording Voice Samples
- **Record Button**: Click or press SPACE to start/stop recording
- **Play Button**: Preview your last recording
- **Next Button**: Save and move to next phrase
- Keyboard shortcuts:
  - `SPACE`: Start/Stop recording
  - `P`: Play last recording
  - `R`: Re-record
  - `N`: Next unrecorded phrase
  - `→`: Skip phrase
  - `←`: Go back
  - `ESC`: Exit (auto-saves progress)

### 2. Starting Training from GUI
Once you have at least 100 recordings:

1. Click the **"🚀 Train Speech-to-Text"** button
2. Confirm the training dialog
3. Training starts automatically with optimized settings:
   - **22 epochs** (instead of 50)
   - **FP16 mixed precision**
   - **Gradient accumulation** (4x)
   - **Gradient checkpointing**
   - **Aggressive memory management**

### 3. Training Progress
- Progress bar shows epoch completion
- Status updates in real-time
- You can continue recording while training runs
- Training takes ~1.5-2 hours

### 4. After Training
- Click **"📄 Last Result"** to view training summary
- Model saved to: `models/monica_finetuned/1986/save/`
- Training log: `models/monica_finetuned/1986/train_log.txt`

## Training Configuration

The GUI uses these optimized settings:
```yaml
Epochs: 22
Precision: fp16
Batch Size: 1
Gradient Accumulation: 4
Gradient Checkpointing: True
Gradient Clipping: 5.0
```

## Memory Optimizations

All CUDA memory fixes are automatically enabled:
- ✅ Mixed precision (FP16) - 50% memory reduction
- ✅ Gradient checkpointing - 30-50% activation memory saved
- ✅ Gradient accumulation - Simulates batch_size=4
- ✅ Aggressive memory clearing - Prevents fragmentation
- ✅ Optimized CUDA allocator - Better memory management

## What to Do After Training

1. **Review Training Metrics**:
   ```bash
   # View last 50 lines of training log
   powershell -command "Get-Content models\monica_finetuned\1986\train_log.txt -Tail 50"
   ```

2. **Check Post-Training Analysis**:
   - See `POST_TRAINING_ANALYSIS_PLAN.md` for next steps
   - Review WER (Word Error Rate) and CER (Character Error Rate)
   - Decide if you need more epochs or adjustments

3. **Test the Model**:
   - The trained model is ready to use
   - Location: `models/monica_finetuned/1986/save/`
   - Integrate into Monica's STT system

## Troubleshooting

### "Training Data Not Ready"
- Record at least 100 phrases first
- CSV files are auto-created at 100+ recordings

### CUDA Out of Memory
- The optimizations should prevent this
- If it still happens:
  1. Reduce `grad_accumulation_factor` to 2 in `hparams_monica.yaml`
  2. Or freeze wav2vec2: set `freeze_wav2vec: True`

### Training Fails
- Check console output for errors
- View log: `models/monica_finetuned/1986/train_log.txt`
- See `MEMORY_OPTIMIZATIONS.md` for troubleshooting

## Monitor GPU During Training

Open a second terminal:
```bash
.venv\Scripts\python.exe monitor_gpu_memory.py
```

This shows real-time GPU memory usage and warns if memory gets too high.

## File Locations

| File | Purpose |
|------|---------|
| `START_VOICE_TRAINING.bat` | Quick launcher (double-click) |
| `launch_voice_training_gui.py` | Python launcher script |
| `monica_ai/voice_training/record_voice.py` | Main GUI code |
| `train_monica.py` | Training script (called by GUI) |
| `hparams_monica.yaml` | Training configuration |
| `MEMORY_OPTIMIZATIONS.md` | Memory optimization details |
| `POST_TRAINING_ANALYSIS_PLAN.md` | Post-training steps |

## Tips

1. **Recording Quality**:
   - Speak clearly and naturally
   - Use a quiet environment
   - Keep consistent distance from mic

2. **Training Strategy**:
   - Start with 100-200 recordings
   - Run first training (22 epochs)
   - Review results
   - Add more recordings if needed
   - Fine-tune settings based on WER

3. **Continue Recording**:
   - You can keep recording while training runs
   - GUI won't block during training
   - All progress is auto-saved

Ready to start? Just double-click `START_VOICE_TRAINING.bat`!
