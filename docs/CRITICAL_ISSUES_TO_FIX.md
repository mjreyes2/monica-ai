# CRITICAL ISSUES - MUST FIX TONIGHT FOR PRESENTATION

## User's Issues (Priority Order)

### 1. DUPLICATE TRANSCRIPTIONS ❌
**Example**: "Monica show yourself lonia show yourself"
**Problem**: Text being repeated/duplicated in transcription
**Impact**: Commands not recognized properly

### 2. PLASMA ORB NOT APPEARING ❌
**Command**: "Monica show yourself"
**Response**: "I can see you, M JP. Would you like me to make myself visible?"
**Problem**: Monica responds but orb doesn't appear
**Missing**: 
- 3D pulsating plasma orb
- Electrical formation sounds
- Orb forming sounds (monica_Orb_forming.mp3, monica_Orb_forming_two.mp3)
- Pulsating sounds (monicaOrb_pulsating.mp3, etc.)

### 3. FACE DETECTION COVERAGE ❌
**Current**: Only showing face
**Required**: Full body coverage
- Face ✓
- Neck ❌
- Shoulders ❌
- Arms ❌
- Torso ❌
- Body ❌
**Purpose**: Monica needs to read/see/understand full body language

### 4. SLOW RESPONSE TIME ❌
**Command**: "Monica initialize"
**Problem**: Took too long to respond
**Expected**: Fast, immediate response

### 5. DETECTORS LAGGING ❌
**Problem**: Video detectors showing slight lag
**Impact**: Real-time analysis not smooth

## Root Causes to Investigate

1. **Duplicate transcriptions**: Likely KenLM or LLM post-processor repeating text
2. **Orb not showing**: Command not triggering orb window display
3. **Face detection**: Camera/detector settings limiting view area
4. **Slow response**: Audio buffer or LLM processing delays
5. **Detector lag**: Frame rate or processing bottleneck

## Files to Check/Fix

- `monica_ai/src/audio/huggingface_asr.py` - Transcription duplicates
- `monica_ai/src/audio/stt_llm_postprocessor.py` - LLM cleanup
- `monica_ai/src/gui/main_window.py` - Orb display commands
- `monica_ai/src/ar/` - Orb window and sounds
- `monica_ai/src/biometric/` - Face/body detection
- `monica_ai/src/camera/` - Camera coverage settings

## Must Work For Presentation

✅ KenLM accuracy (95%+) - DONE
❌ No duplicate transcriptions
❌ Plasma orb appears with sounds
❌ Full body detection
❌ Fast response times
❌ Smooth detector performance
