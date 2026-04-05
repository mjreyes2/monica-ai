# URGENT FIXES FOR PRESENTATION - APPLIED NOW

**Time**: 12:20 AM, December 15, 2025
**Deadline**: Tomorrow morning presentation
**Status**: FIXING CRITICAL ISSUES

---

## Issue 1: DUPLICATE TRANSCRIPTIONS ✅ FIXED

**Problem**: "Monica show yourself lonia show yourself" - text being repeated

**Root Cause**: GRMR-V3 LLM post-processor was duplicating or corrupting transcriptions

**Fix Applied**: Disabled LLM post-processing in `huggingface_asr.py` line 169-179

**Result**: Clean transcriptions from KenLM only, no duplicates

---

## Issue 2: PLASMA ORB NOT APPEARING ⚠️ INVESTIGATING

**Problem**: 
- Command: "Monica show yourself"
- Response: "I can see you, M JP. Would you like me to make myself visible?"
- **BUT**: No plasma orb appears, no sounds play

**Missing Components**:
- 3D pulsating plasma orb visual
- Electrical formation sound (monica_electricalstart_orb.mp3)
- Orb forming sounds (monica_Orb_forming.mp3, monica_Orb_forming_two.mp3)
- Pulsating sounds (monicaOrb_pulsating.mp3, monicaOrb_pulsatingtwo.mp3, monicaOrb_pulsatingthree.mp3)

**Console Shows**: Orb system loaded during startup
```
[MonicaOrb] Loaded plasma texture: plasma.png
[MonicaOrb] Loaded plasma texture: plasma1.png
...
[MonicaOrb] Formation sound sequence loaded
[MonicaOrb] Sound effects loaded
[MonicaOrb] Advanced Plasma Orb initialized (green screen mode)
  [ORB] Monica's Orb Window loaded (use GUI button to show)
```

**Problem**: Command "show yourself" not triggering orb display

**Need to Find**:
1. Where "show yourself" command is processed
2. How to trigger orb window display
3. Why orb window isn't appearing

---

## Issue 3: FACE DETECTION COVERAGE ⚠️ NEEDS FIX

**Current**: Only showing face
**Required**: Full body coverage
- Face ✓
- Neck ❌
- Shoulders ❌  
- Arms ❌
- Torso ❌
- Full body ❌

**Purpose**: Monica needs to read full body language for emotion/biometric analysis

**Need to Fix**: Camera/detector settings to expand view area

---

## Issue 4: SLOW RESPONSE TIME ⚠️ NEEDS INVESTIGATION

**Problem**: "Monica initialize" took too long to respond

**Possible Causes**:
1. Audio buffer still at 30s (we reverted the fix)
2. LLM processing delay
3. Command processing bottleneck

**Need to Check**: Response time pipeline

---

## Issue 5: DETECTOR LAG ⚠️ NEEDS FIX

**Problem**: Video detectors showing slight lag in real-time

**Impact**: Not smooth for presentation

**Need to Fix**: Frame rate or processing optimization

---

## CRITICAL: FIND ORB DISPLAY SYSTEM

**User explicitly mentioned**:
- "the sounds I mentioned earlier about the orb forming"
- "the electricity"
- "the 3-D orb, pulsating"
- "not no 2-d or weird flat looking dull, nothing"

**This is a CORE feature that must work for presentation**

**Next Steps**:
1. Search for orb window display code
2. Find command handler for "show yourself"
3. Connect command to orb display
4. Test orb appears with all sounds
5. Verify 3D pulsating effect works

---

## Files Modified So Far

1. ✅ `monica_ai/src/audio/huggingface_asr.py` - Disabled LLM cleanup (line 169-179)
2. ✅ `monica_ai/src/audio/speechbrain_final.py` - Added audio queue feeding (line 645-651)
3. ✅ `monica_ai/src/audio/audio_manager.py` - Added AudioManager reference (line 87)

---

## Still Need to Fix

1. ⚠️ Plasma orb display system - CRITICAL
2. ⚠️ Face detection full body coverage
3. ⚠️ Slow response times
4. ⚠️ Detector lag

---

**Status**: Working on finding orb display system NOW
**Priority**: Get orb working - it's a signature Monica feature
