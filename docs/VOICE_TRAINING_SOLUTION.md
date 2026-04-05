# Monica Voice Training - Solution Summary

## Problem
- WER (Word Error Rate) stuck at **100%** during Wav2Vec2 fine-tuning
- Model outputting only blank predictions
- Training loss decreased but decoder produced no text

## Root Cause Identified
**Creating a custom vocabulary breaks the pretrained decoder.**

The pretrained `facebook/wav2vec2-base-960h` model has a specific vocabulary (32 tokens: A-Z, space, special tokens). When we created a custom vocabulary with different token IDs, the decoder's learned weights no longer matched, causing it to output only blank tokens.

## Solution Applied
**Use the pretrained model's EXISTING vocabulary instead of creating a custom one.**

### Key Changes:
1. Load processor directly from pretrained model:
   ```python
   processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
   ```

2. Convert transcriptions to UPPERCASE (pretrained vocab uses uppercase):
   ```python
   text = text.upper()
   ```

3. Freeze feature extractor to prevent overfitting:
   ```python
   model.freeze_feature_extractor()
   ```

4. Use low learning rate (1e-5) for stability

## Results
| Metric | Before Fix | After Fix |
|--------|-----------|-----------|
| WER | 100% (stuck) | **~16%** (and improving) |
| Loss | Decreasing | Decreasing |
| Predictions | Blank only | Actual text |

## Dataset
- **3,122 voice recordings** (unified location)
- **~4 hours** of personal voice data
- Location: `voice_training/recordings/MJP/`

## Files
- **Training Script**: `train_wav2vec2_final.py`
- **Model Output**: `models/wav2vec2_final/final_model/`
- **Recordings**: `voice_training/recordings/MJP/`

## How to Use the Trained Model
```python
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import librosa

# Load fine-tuned model
processor = Wav2Vec2Processor.from_pretrained("models/wav2vec2_final/final_model")
model = Wav2Vec2ForCTC.from_pretrained("models/wav2vec2_final/final_model")

# Transcribe audio
audio, sr = librosa.load("audio.wav", sr=16000)
inputs = processor(audio, sampling_rate=16000, return_tensors="pt")
logits = model(**inputs).logits
predicted_ids = logits.argmax(dim=-1)
transcription = processor.batch_decode(predicted_ids)[0]
print(transcription)
```

## Key Lessons Learned
1. **Never create custom vocabulary for pretrained CTC models** - use the model's existing vocab
2. **Freeze feature extractor** for small datasets (<10 hours)
3. **Use low learning rate** (1e-5 or lower) to prevent blank collapse
4. **Match text format** to pretrained vocab (uppercase for wav2vec2-base-960h)

---
*Solution implemented: December 14, 2025*
