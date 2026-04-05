# Voice Training Integration Guide for Monica AI

## Overview

You have recorded **4,071 voice samples** across multiple training batches. This guide explains how to properly fine-tune Whisper with your voice data and integrate it into Monica.

## What You've Recorded

- **Massive English Dataset**: 500+ phrases covering technology, work, home, shopping, health, travel, entertainment, education, nature, emotions, social, time, colors, food, sports
- **Massive Spanish Dataset**: 500+ phrases in Spanish covering the same categories
- **Strong Expressions**: 120 phrases including curse words and emotional expressions in both languages
- **Natural Conversation**: 120 conversational phrases
- **English Batch 2**: 120 additional English phrases
- **Spanish Batch 2**: 120 additional Spanish phrases
- **Original Recordings**: 561 initial phrases

**Total: 4,071 voice recordings** in `voice_recordings/` directory

## The Problem with Previous Approach

The `fine_tune_whisper_simple.py` script was NOT actually fine-tuning. It was only:
1. Transcribing your audio with the base model
2. Extracting vocabulary from transcriptions

This did NOT improve Whisper's ability to recognize YOUR voice - it just created a vocabulary list.

## The Solution: Proper Fine-Tuning

The new `fine_tune_whisper_proper.py` script implements REAL fine-tuning based on HuggingFace's official guide:

### What It Does

1. **Loads all 4,071 voice recordings** from `voice_recordings/`
2. **Extracts transcriptions from filenames** (e.g., `phrase_001_monica_initialize.wav` → "monica initialize")
3. **Prepares a proper dataset** with audio and text pairs
4. **Splits into 80% train / 20% test** for proper evaluation
5. **Fine-tunes the Whisper base model** on your voice data
6. **Saves the fine-tuned model** for use in Monica

### Key Differences from Simple Approach

| Aspect | Simple Script | Proper Script |
|--------|---------------|---------------|
| Fine-tuning | ❌ No | ✅ Yes |
| Model improvement | ❌ No | ✅ Yes (learns your voice) |
| Training | ❌ No | ✅ Full training loop |
| Evaluation | ❌ No | ✅ WER metrics |
| Integration | ❌ Manual | ✅ Automatic |

## Step-by-Step Integration

### Step 1: Install Dependencies

```bash
cd c:\Users\mxz\monica_project\monica_ai
pip install torch datasets transformers soundfile librosa jiwer evaluate
```

### Step 2: Run Fine-Tuning

```bash
python fine_tune_whisper_proper.py
```

**What to expect:**
- Model download: ~500MB (first time only)
- Data preparation: 2-5 minutes
- Fine-tuning: 30-60 minutes (depends on GPU)
- Output: `whisper_finetuned_personal/final_model/`

**Progress indicators:**
```
[1/5] Preparing dataset...
[2/5] Loading Whisper model and processor...
[3/5] Processing audio and text data...
[4/5] Setting up training...
[5/5] Starting fine-tuning...
```

### Step 3: Update Monica Configuration

Edit `config.json` in the monica_ai directory:

```json
{
  "stt": {
    "engine": "whisper",
    "whisper_model": "./whisper_finetuned_personal/final_model",
    "language": "en",
    "energy_threshold": 0.005,
    "pause_threshold": 3.5,
    "phrase_time_limit": 120.0
  }
}
```

**OR** pass the path when initializing the recognizer in code:

```python
from src.audio.faster_speech_recognition import FasterSpeechRecognizer

recognizer = FasterSpeechRecognizer(
    model_size="base",
    fine_tuned_model_path="./whisper_finetuned_personal/final_model"
)
```

### Step 4: Restart Monica

```bash
python main.py
```

Monica will now use your fine-tuned model!

## What Happens During Fine-Tuning

### Data Preparation Phase
- Loads 4,071 WAV files from `voice_recordings/`
- Extracts phrase from filename (e.g., "monica initialize")
- Resamples audio to 16kHz (Whisper standard)
- Creates dataset with audio/text pairs
- Splits: 3,256 training samples, 815 test samples

### Training Phase
- Freezes Whisper encoder (saves memory)
- Fine-tunes decoder on your voice
- Uses mixed precision (fp16) if CUDA available
- Trains for 5 epochs
- Evaluates every epoch using WER (Word Error Rate)
- Saves best model based on WER

### Output
```
whisper_finetuned_personal/
├── final_model/
│   ├── config.json
│   ├── preprocessor_config.json
│   ├── pytorch_model.bin
│   ├── tokenizer.json
│   ├── tokenizer_config.json
│   └── ...
└── checkpoint-*/
    └── (intermediate checkpoints)
```

## Expected Improvements

After fine-tuning with 4,071 samples, you should see:

✅ **Better recognition of your voice patterns**
- Whisper learns your accent, speech rate, pronunciation

✅ **Improved accuracy for trained phrases**
- All 4,071 phrases will be recognized more accurately

✅ **Better handling of your vocabulary**
- Technical terms, names, and phrases you use frequently

✅ **Reduced hallucinations**
- Model is trained specifically on YOUR voice, not generic speech

## Troubleshooting

### Issue: "CUDA out of memory"
**Solution:** Reduce batch size in `fine_tune_whisper_proper.py`:
```python
per_device_train_batch_size=2,  # Reduce from 4
```

### Issue: "Fine-tuned model not found"
**Solution:** Check the path in config.json is correct:
```bash
# Verify the model exists
ls whisper_finetuned_personal/final_model/
```

### Issue: "No WAV files found"
**Solution:** Ensure voice recordings are in the correct directory:
```bash
# Check recordings exist
ls voice_recordings/ | wc -l  # Should show 4071
```

### Issue: Fine-tuning is very slow
**Solution:** 
- Use GPU: Install CUDA and cuDNN
- Reduce number of epochs in script
- Use smaller batch size

## Advanced: Custom Training Parameters

Edit `fine_tune_whisper_proper.py` to customize:

```python
# Training duration
num_train_epochs=5,  # Increase for more training

# Learning rate (lower = slower but more stable)
learning_rate=1e-5,

# Batch size (larger = faster but needs more VRAM)
per_device_train_batch_size=4,

# Evaluation frequency
evaluation_strategy="epoch",  # or "steps"
```

## Monitoring Training

Training logs are saved to `runs/` directory:

```bash
# View training progress
tensorboard --logdir=runs/
```

Then open http://localhost:6006 in your browser.

## Files Involved

### New Files Created
- `fine_tune_whisper_proper.py` - Main fine-tuning script (PROPER implementation)
- `whisper_finetuned_personal/` - Output directory with fine-tuned model

### Modified Files
- `src/audio/faster_speech_recognition.py` - Added `fine_tuned_model_path` parameter
- `config.json` - Update with fine-tuned model path

### Existing Files (Not Changed)
- `voice_recordings/` - Your 4,071 voice samples (unchanged)
- `fine_tune_whisper.py` - Old implementation (kept for reference)
- `fine_tune_whisper_simple.py` - Simple version (kept for reference)

## Next Steps

1. **Run fine-tuning**: `python fine_tune_whisper_proper.py`
2. **Update config**: Set `whisper_model` path in `config.json`
3. **Restart Monica**: `python main.py`
4. **Test**: Say your trained phrases and verify improved accuracy

## Support

If you encounter issues:

1. Check the terminal output for error messages
2. Verify all dependencies are installed: `pip list | grep -E "torch|transformers|datasets"`
3. Ensure voice_recordings/ has 4,071 files: `ls voice_recordings/ | wc -l`
4. Check GPU availability: `nvidia-smi` (if using CUDA)

## References

- HuggingFace Fine-Tuning Guide: https://huggingface.co/blog/fine-tune-whisper
- Whisper Model Card: https://huggingface.co/openai/whisper-base
- faster-whisper: https://github.com/guillaumekln/faster-whisper
