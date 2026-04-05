# TRANSCRIPTION ACCURACY ISSUE - ANALYSIS

**Time**: 12:35 AM, December 15, 2025
**User Report**: "Transcript is horrible, continues to be horrible on the screen"

---

## CURRENT SETUP

### What's Loaded
1. **HuggingFace Wav2Vec2 Model** - Custom trained on user's voice (3,122 recordings, WER 14.59%)
2. **KenLM Language Model** - 3-gram English model for context-aware decoding
3. **STT Accuracy Enhancer** - Noise reduction, speed normalization

### Transcription Pipeline
```
Audio Input 
  → SpeechBrain FinalMonicaAudio (speechbrain_final.py line 730)
  → FinalSpeechBrainRecognizer.recognize_tensor() (line 387)
  → HuggingFaceASR.transcribe_tensor() (huggingface_asr.py line 114)
  → KenLM decode_with_lm() (line 158) OR greedy decode (line 167)
  → Return transcription.lower().strip() (line 181)
```

---

## POTENTIAL ISSUES

### Issue 1: KenLM May Not Be Working
**Evidence**: Console should show "[HUGGINGFACE-ASR] Used KenLM decoding" but user may not be seeing this

**Check**: 
- Is KenLM actually being used? (line 154-159)
- Is `self.use_lm` set to True?
- Is `self.lm_decoder` properly initialized?

**Possible Problem**: KenLM initialization may have failed silently

### Issue 2: Audio Quality
**Evidence**: User mentions transcription is "horrible"

**Possible Causes**:
- Microphone too far/close
- Background noise
- Audio buffer issues
- Sample rate mismatch

### Issue 3: Model Mismatch
**Evidence**: Model trained on user's voice but may not match current audio conditions

**Possible Causes**:
- Training data was in different environment
- Different microphone used for training vs runtime
- Audio preprocessing differences

### Issue 4: LLM Post-Processing Disabled
**Status**: We disabled GRMR-V3 to fix duplicates

**Impact**: No grammar cleanup, which could make transcriptions look worse even if technically accurate

---

## WHAT USER SEES

**Without LLM cleanup**, transcriptions come out as:
- All lowercase
- No punctuation
- No capitalization
- Raw output from KenLM/greedy decoder

**Example**:
- Input: "Monica show yourself"
- Output: "monica show yourself" (looks unprofessional)
- With duplicates bug: "monica show yourself lonia show yourself"

---

## ROOT CAUSE ANALYSIS

### Most Likely Issue: **KenLM Not Actually Being Used**

**Why**:
1. KenLM initialization may have failed due to "duplicate entries" error
2. We fixed the vocabulary mapping, but need to verify it's actually working
3. Console logs should show "Used KenLM decoding" but user may not be seeing this

### Secondary Issue: **No Post-Processing**

**Why**:
1. We disabled LLM cleanup to fix duplicates
2. Now transcriptions are raw, lowercase, no punctuation
3. This makes them look "horrible" even if technically accurate

---

## SOLUTION OPTIONS

### Option 1: Verify KenLM is Working
**Action**: Add more logging to confirm KenLM is being used
**Check**: Console output for "[HUGGINGFACE-ASR] Used KenLM decoding"

### Option 2: Re-enable Basic Cleanup (Not LLM)
**Action**: Add simple post-processing without GRMR-V3
- Capitalize first letter
- Capitalize "Monica", "I"
- Add period at end
- Fix common contractions

### Option 3: Train More Voice Data
**User Question**: "Do I need to train the STT more with my voice?"

**Answer**: 
- Current model: 3,122 recordings, WER 14.59% (very good)
- More training could help but unlikely to be the issue
- Problem is more likely in the decoding/post-processing pipeline

### Option 4: Use Different Decoding Strategy
**Action**: Try different KenLM parameters
- Adjust beam width
- Adjust language model weight (alpha)
- Adjust word insertion penalty (beta)

---

## IMMEDIATE ACTION NEEDED

1. **Check Console Logs**: Look for "Used KenLM decoding" messages
2. **Test Transcription**: Say a clear sentence and see exact output
3. **Add Basic Cleanup**: Simple capitalization/punctuation without LLM
4. **Verify KenLM**: Ensure language model is actually being used

---

## RECOMMENDED FIX

**Add simple post-processing** that doesn't use GRMR-V3:

```python
def _basic_cleanup(text: str) -> str:
    """Simple cleanup without LLM"""
    if not text:
        return text
    
    # Capitalize first letter
    text = text[0].upper() + text[1:] if text else text
    
    # Capitalize Monica
    text = text.replace('monica', 'Monica')
    
    # Capitalize I
    import re
    text = re.sub(r'\bi\b', 'I', text)
    
    # Add period if missing
    if text and text[-1] not in '.!?':
        text += '.'
    
    return text
```

This would transform:
- "monica show yourself" → "Monica show yourself."
- "monica what time is it" → "Monica what time is it."

Much more professional without risk of duplicates.

---

**Next Step**: Ask user for example of what they're seeing vs what they expect
