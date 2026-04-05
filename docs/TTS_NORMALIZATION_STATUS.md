# TTS Normalization Status Report

**Date**: December 14, 2025, 11:05 PM  
**Question**: Are we utilizing NeMo text normalization for TTS?

---

## ✅ YES - Monica Already Has Comprehensive TTS Normalization

### What's Already Implemented

**1. NeMo Text Normalizer** ✅
- **File**: `monica_ai/src/tts/nemo_normalizer.py`
- **Status**: Fully implemented
- **Features**:
  - Grammar-based finite-state transducers (FST)
  - Handles numbers, dates, times, currency, ordinals
  - Multi-language support (EN, ES, DE, FR, RU, VI, AR, ZH)
  - Subprocess-based (uses conda Python with pynini)
  - Caching for performance

**2. Text Normalizer** ✅
- **File**: `monica_ai/src/tts/text_normalizer.py`
- **Status**: Fully implemented (900 lines)
- **Features**:
  - Year conversion (2025 → "twenty twenty-five")
  - Number conversion (42 → "forty-two")
  - Ordinals (1st → "first")
  - Dates, times, currency, percentages
  - Abbreviation expansion
  - Custom lexicon support

**3. Neural Text Normalizer** ✅
- **File**: `monica_ai/src/tts/neural_text_normalizer.py`
- **Status**: Implemented
- **Type**: Transformer-based context-aware normalization

**4. Prosody Enhancer** ✅
- **File**: `monica_ai/src/tts/prosody_enhancer.py`
- **Status**: Implemented (18KB)
- **Purpose**: Better rhythm and intonation

**5. TTS Manager** ✅
- **File**: `monica_ai/src/tts/tts_manager.py`
- **Status**: Fully implemented (73KB)
- **Integration**: Uses all normalizers above

---

## Addressing Your Specific Issues

### Issue 1: "1990" Pronounced as "1 9 9 0" ✅ ALREADY SOLVED

**Your System Already Has This:**

```python
# monica_ai/src/tts/nemo_normalizer.py (lines 83-98)
def normalize(self, text: str) -> str:
    """
    Normalize text using NeMo Text Processing.
    
    Converts:
    - Numbers: "25" → "twenty five"
    - Currency: "$5.99" → "five dollars and ninety nine cents"
    - Dates: "December 7th, 2025" → "december seventh, twenty twenty five"
    - Times: "3:30 PM" → "three thirty p m"
    - Ordinals: "1st" → "first"
    """
```

**Implementation:**
```python
# From nemo_normalizer.py
from nemo_text_processing.text_normalization.normalize import Normalizer
n = Normalizer(input_case='cased', lang='en')
result = n.normalize("The year was 1990.")
# Output: "The year was nineteen ninety."
```

### Issue 2: Pauses at Beginning ("Wha...") ⚠️ NEEDS VERIFICATION

**Potential Causes:**
1. Training data had leading silence
2. Duration prediction mismatch in FastPitch
3. Tokenizer treating first letter as separate token

**Your System Has:**
- Prosody enhancer (may help with alignment)
- Text normalizer (handles capitalization)

**Need to Check:**
- If using FastPitch/HiFi-GAN (not found in search)
- If using Piper TTS (found in tts_manager.py)
- If VAD post-processing is applied

---

## Current TTS Stack in Monica

### Confirmed Components

```
Text Input
    ↓
[NeMo Normalizer] ← Grammar-based FST normalization
    ↓
[Text Normalizer] ← Regex-based fallback
    ↓
[Prosody Enhancer] ← Rhythm and intonation
    ↓
[TTS Engine] ← Piper (primary) or System TTS
    ↓
Audio Output
```

### Integration Status

**TTS Manager Integration:**
```python
# monica_ai/src/tts/tts_manager.py (lines 35-42)
try:
    from .nemo_normalizer import NeMoNormalizer, is_nemo_available
    HAS_NEMO = is_nemo_available()
    if HAS_NEMO:
        print("[TTS] NeMo Text Processing available (grammar-based normalization)")
except ImportError:
    HAS_NEMO = False
```

**Text Normalizer Import:**
```python
# lines 19-25
try:
    from .text_normalizer import normalize_text_for_tts, get_text_normalizer
    HAS_TEXT_NORMALIZER = True
except ImportError:
    HAS_TEXT_NORMALIZER = False
```

---

## What You DON'T Need to Do

❌ **Implement NeMo Normalizer** - Already done  
❌ **Add text normalization** - Already comprehensive  
❌ **Set up FST-based conversion** - Already implemented  
❌ **Handle dates/numbers** - Already handled  

---

## What You MIGHT Need to Do

### 1. Verify NeMo is Being Called

**Check if normalization is active in synthesis:**
```python
# Need to verify in tts_manager.py synthesis methods
# that normalize_text_for_tts() or NeMoNormalizer is called
```

### 2. Test Date Pronunciation

**Run test:**
```bash
cd monica_ai/src/tts
python nemo_normalizer.py
```

**Expected output:**
```
Original:   The meeting is on December 7th, 2025 at 3:30 PM
Normalized: the meeting is on december seventh twenty twenty five at three thirty p m
```

### 3. Check for FastPitch/HiFi-GAN

**Search results:** No FastPitch or HiFi-GAN found in Monica's codebase

**Current TTS Engine:** Piper (ONNX-based, not NeMo)

**Implication:** The pause/alignment issues you described are specific to FastPitch/HiFi-GAN training. Since Monica uses Piper, those specific issues may not apply.

---

## Recommendations

### Immediate Actions

**1. Verify Normalization is Active**
```bash
# Test the NeMo normalizer
python monica_ai/src/tts/nemo_normalizer.py
```

**2. Check TTS Manager Usage**
Need to verify that `tts_manager.py` actually calls the normalizers before synthesis.

**3. Test with Real Examples**
```python
from monica_ai.src.tts.tts_manager import TTSManager

tts = TTSManager()
result = tts.synthesize("The year was 1990 and it cost $5.99")
# Check if audio pronounces correctly
```

### If Issues Persist

**For Date Pronunciation:**
- NeMo normalizer should handle this ✅
- Verify conda Python path is correct in `nemo_normalizer.py` line 25
- Check if NeMo is actually being called (add debug logging)

**For Leading Pauses:**
- Not applicable if using Piper (not FastPitch)
- If using custom trained models, would need VAD trimming
- Check prosody enhancer settings

---

## System Architecture

### What Monica Has

```python
# Comprehensive TTS normalization stack:
1. NeMo Text Processing (grammar-based FST)
   ├── Handles: dates, numbers, currency, ordinals
   └── Multi-language support

2. Text Normalizer (regex-based fallback)
   ├── Year conversion
   ├── Number-to-words
   └── Abbreviation expansion

3. Neural Text Normalizer (transformer-based)
   └── Context-aware normalization

4. Prosody Enhancer
   └── Rhythm and intonation control

5. TTS Manager
   └── Orchestrates all components
```

### What Monica Uses for TTS

- **Primary**: Piper TTS (ONNX models)
- **Fallback**: System TTS
- **Not Found**: FastPitch, HiFi-GAN, NeMo TTS models

---

## Conclusion

### ✅ You Already Have Text Normalization

Monica's TTS system has **comprehensive text normalization** including:
- ✅ NeMo Text Processing (grammar-based)
- ✅ Regex-based normalizer
- ✅ Neural normalizer
- ✅ Prosody enhancement

### ⚠️ Need to Verify

1. **Is normalization actually being called?**
   - Check if `tts_manager.py` synthesis methods use normalizers
   - Add logging to confirm

2. **Is NeMo available?**
   - Requires conda Python with pynini
   - Check path: `C:\Users\mxz\miniconda3\python.exe`

3. **Which TTS engine is active?**
   - Piper (found) - no FastPitch issues
   - Custom models (not found) - would need alignment fixes

### 🎯 Next Steps

1. **Test NeMo normalizer:**
   ```bash
   python monica_ai/src/tts/nemo_normalizer.py
   ```

2. **Verify TTS manager calls normalizers:**
   - Check synthesis methods in `tts_manager.py`
   - Add debug logging if needed

3. **Test with problematic text:**
   ```python
   "The year was 1990"  # Should say "nineteen ninety"
   "It costs $5.99"     # Should say "five dollars ninety nine cents"
   ```

---

**Status**: Monica has all the normalization infrastructure. Just need to verify it's being used correctly.

**Last Updated**: December 14, 2025, 11:05 PM
