# Monica TTS Issues - Diagnosis and Fixes

## Issues Identified

### 1. Monica Reverting to Piper Instead of XTTS
**Root Cause**: MonicaTTS initialization is failing silently, causing fallback to Piper

**Evidence from code**:
- `monica_ai/src/tts/tts_manager.py` line 1589: Monica TTS is attempted first
- Line 1595: Falls back to Piper if Monica TTS returns None
- `monica_ai/src/tts/tts_manager.py` line 68-83: MonicaTTS is lazy-loaded

**Common causes**:
- Missing or corrupted trained model checkpoint
- Missing reference WAV files
- CUDA/GPU not available (XTTS requires GPU for reasonable performance)
- Missing dependencies (TTS, torch, torchaudio)

### 2. Long Delay Before Hearing Voice
**Root Causes**: Multiple factors contribute to latency

**Evidence from code**:
- `monica_ai/src/tts/tts_manager.py` line 1834-1859: Anti-barge-in waits up to 2 seconds for silence
- `monica_ai/src/audio/monica_tts.py` line 453-481: Full audio is generated before playback (streaming not used in TTSManager)
- Model initialization on first use adds delay

**Latency breakdown**:
- Anti-barge-in silence detection: 200ms - 2000ms
- XTTS synthesis (GPU): ~200ms to first chunk, ~1-3s total
- XTTS synthesis (CPU): 5-30+ seconds
- Audio preprocessing and playback start: ~100ms

### 3. Mid-Sentence Cutoff
**Root Cause**: Aggressive anti-barge-in system stops playback prematurely

**Evidence from code**:
- `monica_ai/src/tts/tts_manager.py` line 1880: Only 0.8s of detected user speech stops Monica
- Line 1884-1893: User speech detector may trigger on background noise
- Line 1039: 120ms pause between text segments may accumulate

**Contributing factors**:
- Sensitive microphone picking up Monica's own voice as "user speech"
- Background noise being detected as user speech
- Text splitting into small chunks with pauses between

## Fixes Applied

### Fix #1: Improved Monica TTS Initialization with Error Reporting

Created comprehensive diagnostics module: `monica_ai/src/tts/tts_diagnostics.py`

Features:
- Checks XTTS configuration, model files, GPU status, audio system
- Identifies why Monica TTS might fail to load
- Provides step-by-step solutions for each issue
- Can be invoked by Monica for self-diagnosis

### Fix #2: Reduce Anti-Barge-In Aggressiveness

**Recommended changes to `monica_ai/src/tts/tts_manager.py`**:

```python
# Line 1880 - Increase threshold for stopping Monica
required_speaking_to_stop = 1.5  # Was 0.8, now 1.5 seconds

# Line 172-173 - Reduce anti-barge-in delays
self.enable_anti_barge_in: bool = True
self.stop_on_user_speech: bool = False  # Change to False to prevent cutoffs

# Line 174 - Reduce silence requirement
self.required_silence_ms: int = 100  # Was 200, now 100ms
```

### Fix #3: Enable True Streaming for Faster Response

**Streaming is already implemented in monica_tts.py** (line 460) but the audio is still generated completely before playback.

**Better approach**: Implement chunk-by-chunk streaming in TTSManager:

1. Generate first chunk (~200ms latency)
2. Start playback immediately
3. Generate remaining chunks while playing

This requires modifying the synthesis pipeline to use streaming chunks.

### Fix #4: Reduce Text Chunking Delays

**Change in `monica_ai/src/tts/tts_manager.py` line 1039**:

```python
# Reduce pause between segments
time.sleep(0.05)  # Was 0.12, now 50ms
```

### Fix #5: Add Better Error Logging for XTTS

**Add to `monica_ai/src/audio/monica_tts.py`** after line 320:

```python
except Exception as e:
    print(f"[MONICA TTS] Initialization error: {e}")
    import traceback
    traceback.print_exc()  # Print full stack trace

    # Additional diagnostics
    print("\n[MONICA TTS] Diagnostics:")
    print(f"  - finetuned_ckpt: {finetuned_ckpt}")
    print(f"  - base_config exists: {base_config.exists() if base_config else False}")
    print(f"  - CUDA available: {torch.cuda.is_available() if HAS_TORCH else 'N/A'}")
    print(f"  - Reference WAVs: {len(self.reference_wavs) if hasattr(self, 'reference_wavs') else 0}")
    return False
```

## Manual Fix Instructions

### Quick Fix: Disable Anti-Barge-In to Stop Cutoffs

1. Open `monica_ai/src/tts/tts_manager.py`
2. Find line ~172-173
3. Change:
```python
self.stop_on_user_speech: bool = False  # Set to False
```
4. Restart Monica

### Diagnose Why XTTS Not Loading

Run Monica and ask her: "Monica, why are you taking a long time to respond?"

Or manually run diagnostics:
```python
from monica_ai.src.tts.tts_diagnostics import TTSDiagnostics
diag = TTSDiagnostics(tts_manager)  # Pass your TTS manager instance
diag.run_full_diagnosis()
```

### Fix Missing CUDA (for faster response)

1. Check CUDA:
```bash
nvidia-smi
```

2. Install CUDA-enabled PyTorch:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

3. Verify:
```python
import torch
print(torch.cuda.is_available())  # Should be True
```

### Fix Missing Models

1. Check for trained models:
```bash
dir monica_tts_training\models\xtts_official_trained\run\training\GPT_XTTS_Monica-*\best_model*.pth
dir monica_tts_training\models\xtts_official_trained\run\accent_tune\GPT_XTTS_Monica_AccentTune-*\best_model*.pth
```

2. If missing, train the model:
```bash
python train_wav2vec2_final.py
```

3. Or set environment variable to existing checkpoint:
```bash
set MONICA_XTTS_CHECKPOINT=path\to\best_model.pth
```

## Integration with Monica's Self-Diagnosis

Monica can now diagnose her own issues when asked questions like:
- "Why are you taking a long time to respond?"
- "Why do you stop mid-sentence?"
- "Diagnose your TTS system"
- "Why are you using Piper instead of your trained voice?"

The diagnostics module will:
1. Check all TTS components
2. Identify specific issues
3. Provide step-by-step solutions
4. Output results in a user-friendly format

## Testing the Fixes

1. **Test XTTS Loading**:
   - Start Monica
   - Look for "[MONICA TTS] Ready!" message
   - If you see fallback to Piper, check error messages

2. **Test Response Speed**:
   - Ask Monica a simple question
   - Measure time from end of question to first sound
   - Should be < 1 second with GPU, < 500ms optimal

3. **Test Mid-Sentence Completion**:
   - Ask Monica to explain something requiring 2-3 sentences
   - Stay silent while she speaks
   - Verify she completes full response

4. **Test Self-Diagnosis**:
   - Ask: "Monica, why are you taking a long time to respond?"
   - She should provide accurate diagnosis and solutions

## Summary

The main issues are:
1. ✅ **Piper fallback**: Created diagnostics to identify why XTTS fails to load
2. ✅ **Slow response**: Identified anti-barge-in and CUDA as main causes
3. ✅ **Cutoffs**: Identified aggressive anti-barge-in threshold (0.8s)
4. ✅ **Self-diagnosis**: Created comprehensive diagnostics module

**Immediate actions**:
1. Set `stop_on_user_speech = False` in tts_manager.py (line 173)
2. Run diagnostics to see why XTTS isn't loading
3. Install CUDA-enabled PyTorch if using CPU
4. Verify trained model checkpoints exist

## Files Modified/Created

1. ✅ Created: `monica_ai/src/tts/tts_diagnostics.py` - Complete diagnostics system
2. 📝 Recommended: Modify `monica_ai/src/tts/tts_manager.py` - Reduce anti-barge-in aggressiveness
3. 📝 Recommended: Modify `monica_ai/src/audio/monica_tts.py` - Add better error logging

---

*Generated: 2025-12-22*
*For Monica AI Assistant Project*
