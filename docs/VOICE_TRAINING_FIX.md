# Monica AI: Voice Training Integration Fix

**Date:** 2025-12-12
**Issue:** SpeechBrain timeout + Voice training not integrated

---

## Current Problems

### 1. SpeechBrain Loading Timeout
- **Symptom:** 180-second timeout, never loads
- **Root Cause:** Permission errors creating directories
- **Error:** `[WinError 5] Access is denied: 'personal_voice_model'`

### 2. Voice Training Not Integrated
- **Current:** Uses generic `speechbrain/asr-crdnn-rnnlm-librispeech` model
- **Problem:** Trained models are never loaded
- **Missing:** Integration between training and recognition

### 3. No Trained Models Exist
- No checkpoint files found
- Training has never completed
- Voice signature exists but isn't used

---

## Immediate Fix: Permission Errors

### Step 1: Run as Administrator

```cmd
# Right-click your terminal/IDE and select "Run as Administrator"
```

### Step 2: Fix Directory Permissions

```cmd
cd C:\Users\mxz\monica_project\monica_ai

# Create directories with proper permissions
mkdir personal_voice_model
mkdir personal_voice_model\hf_cache
mkdir personal_voice_model\hf_cache\hub
mkdir personal_voice_model\hf_cache\transformers
mkdir personal_voice_model\hf_cache\torch

# Create other needed directories
mkdir models
mkdir data
mkdir model_checkpoints
```

### Step 3: Test SpeechBrain Loading

```cmd
.venv\Scripts\python.exe -c "from monica_ai.src.audio.speechbrain_final import FinalSpeechBrainRecognizer; import time; r = FinalSpeechBrainRecognizer(); time.sleep(30); print('Status:', r.get_loading_status())"
```

**Expected output:**
```
[FINAL-SPEECHBRAIN] Starting model loading with GPU acceleration...
[FINAL-SPEECHBRAIN] ASR model loaded in 12.5s on cuda
[FINAL-SPEECHBRAIN] Speaker model loaded in 3.2s
[FINAL-SPEECHBRAIN] All models loaded successfully in 15.7s
Status: Ready
```

---

## Long-term Fix: Voice Training Integration

### Current Architecture (WRONG)

```
Voice Training System          Speech Recognition
     ↓                                ↓
[Record Phrases]              [Generic Model]
     ↓                                ↓
[Train Model]                  [Recognize Speech]
     ↓                                ↓
[Save to models/]              [NOT USING TRAINING!]
     ↓
[NEVER LOADED!]
```

### What Needs to Happen

#### Option A: Simple Fix - Use Generic Model (Current)
**Pros:**
- Works immediately after permission fix
- No training needed
- Fast loading (15-20s)

**Cons:**
- Not personalized to your voice
- May have accuracy issues with "Monica" wake word

#### Option B: Full Voice Training Integration (Recommended)
**Requires:**
1. Complete voice training (1000+ phrases)
2. Modify `speechbrain_final.py` to load custom model
3. Test custom model accuracy

---

## Steps to Enable Voice Training

### 1. Check Current Recordings

```cmd
cd monica_ai\voice_training\recordings\MJP
dir *.wav /s
```

**How many recordings do you have?**
- < 10: Not enough
- 10-50: Basic training possible
- 50-100: Good training
- 100-500: Very good
- 500+: Excellent
- 1000+: Professional-grade

### 2. Record More Phrases (If Needed)

```cmd
.venv\Scripts\python.exe monica_ai\voice_training\record_voice.py
```

### 3. Train the Model

```cmd
.venv\Scripts\python.exe monica_ai\voice_training\train_speechbrain_wrapper.py
```

**This will:**
- Take 30-60 minutes
- Create model at `models/monica_finetuned/1986/save/`
- Show training progress

### 4. Modify speechbrain_final.py to Load Custom Model

**Current (line 104-108):**
```python
self.asr_model = EncoderDecoderASR.from_hparams(
    source="speechbrain/asr-crdnn-rnnlm-librispeech",  # Generic!
    savedir=str(self.asr_cache_dir),
    run_opts={"device": device}
)
```

**Change to:**
```python
# Check if custom trained model exists
custom_model_dir = self.model_dir.parent / "models" / "monica_finetuned" / "1986" / "save"
if custom_model_dir.exists():
    print(f"[FINAL-SPEECHBRAIN] Loading CUSTOM trained model from {custom_model_dir}")
    self.asr_model = EncoderDecoderASR.from_hparams(
        source=str(custom_model_dir),  # Your trained model!
        savedir=str(self.asr_cache_dir),
        run_opts={"device": device}
    )
else:
    print("[FINAL-SPEECHBRAIN] Loading generic pre-trained model")
    self.asr_model = EncoderDecoderASR.from_hparams(
        source="speechbrain/asr-crdnn-rnnlm-librispeech",
        savedir=str(self.asr_cache_dir),
        run_opts={"device": device}
    )
```

---

## Verification

### Test Generic Model (After Permission Fix)

```cmd
.venv\Scripts\python.exe monica_ai\src\audio\speechbrain_final.py
```

Should load in 15-20 seconds and recognize speech.

### Test Custom Model (After Training)

Same command, but should show:
```
[FINAL-SPEECHBRAIN] Loading CUSTOM trained model from ...
```

---

## Quick Decision Matrix

| Scenario | Action |
|----------|--------|
| Just want it working NOW | Fix permissions, use generic model |
| Want personalized recognition | Record 100+ phrases, train model |
| Need perfect "Monica" detection | Record 1000+ phrases, train model |
| Testing/Development | Use generic model |
| Production/Daily Use | Use trained model |

---

## Next Steps

1. **RIGHT NOW:** Fix permissions (run as admin, create directories)
2. **Test:** Run SpeechBrain loading test
3. **Decide:** Generic model or custom training?
4. **If training:** How many recordings do you have?

Let me know which path you want to take!
