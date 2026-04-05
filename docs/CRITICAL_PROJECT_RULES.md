# CRITICAL PROJECT RULES FOR MONICA AI
## ABSOLUTE RULES - HIGHEST PRIORITY - SET IN STONE

**These rules apply to ALL AI assistants working on this project.**
**These rules OVERRIDE all other considerations including time, complexity, and convenience.**

---

## 🚨 RULE #1: NEVER USE GENERIC PRE-TRAINED MODELS

### FORBIDDEN ACTIONS:
- ❌ **NEVER** fall back to generic pre-trained SpeechBrain models
- ❌ **NEVER** use `speechbrain/asr-crdnn-rnnlm-librispeech`
- ❌ **NEVER** use `speechbrain/asr-wav2vec2-commonvoice-en`
- ❌ **NEVER** suggest using any model other than Monica's custom trained model
- ❌ **NEVER** take shortcuts by reverting to generic solutions
- ❌ **NEVER** simplify problems by removing custom training

### REQUIRED ACTIONS WHEN ENCOUNTERING ISSUES:
1. ✅ **RESEARCH** the problem on GitHub (speechbrain/speechbrain issues)
2. ✅ **SEARCH** Stack Overflow for SpeechBrain CTC issues
3. ✅ **CHECK** Reddit (r/MachineLearning, r/speechtech)
4. ✅ **READ** SpeechBrain documentation thoroughly
5. ✅ **REVIEW** academic papers on wav2vec2 and CTC decoding
6. ✅ **DEBUG** the custom model code to find the root cause
7. ✅ **FIX** the issue while preserving the custom model
8. ✅ **MODIFY** code to work with custom model, never replace it

### RATIONALE:
- User invested significant time recording **1,113 voice samples**
- Custom model is trained specifically for user's voice
- Generic models lack personalization and accuracy
- This work is **SACRED** and must be preserved

### THIS RULE OVERRIDES:
- Time constraints
- Complexity concerns
- Convenience
- Quick fixes
- Simplification attempts
- Any other consideration

---

## 📋 CUSTOM MODEL DETAILS

**Location:** `c:\Users\mxz\monica_project\models\monica_finetuned\1986\`
**Training Data:** 1,113 voice recordings
**Model Type:** wav2vec2 + CTC (facebook/wav2vec2-large-960h-lv60-self)
**Hyperparameters:** `c:\Users\mxz\monica_project\hparams_monica.yaml`
**Label Encoder:** 29 tokens (characters + blank)

---

## 🔧 TROUBLESHOOTING PROTOCOL

When custom model fails:

1. **DO NOT** suggest generic model fallback
2. **DO** read error messages carefully
3. **DO** check tensor shapes and dimensions
4. **DO** verify label encoder configuration
5. **DO** test CTC decoder logic
6. **DO** research the specific error online
7. **DO** fix the underlying issue
8. **DO** preserve all custom training work

---

## 💾 ENFORCEMENT

This rule is stored in:
- This file: `CRITICAL_PROJECT_RULES.md`
- AI Memory System (permanent)
- Code comments in `speechbrain_final.py`

**ANY AI WORKING ON THIS PROJECT MUST FOLLOW THESE RULES.**

The custom model is the **ONLY** acceptable solution. Period.

---

## 🔍 RULE #2: RESEARCH-FIRST APPROACH FOR ALL PROBLEMS

### FORBIDDEN APPROACHES:
- ❌ **NEVER** simplify problems by removing features
- ❌ **NEVER** take shortcuts that bypass the real issue
- ❌ **NEVER** revert to simpler/basic implementations
- ❌ **NEVER** assume "it's too complex" and downgrade
- ❌ **NEVER** give up and suggest workarounds instead of fixes
- ❌ **NEVER** make quick fixes without understanding root cause

### REQUIRED APPROACH FOR EVERY PROBLEM:
1. ✅ **RESEARCH** the exact error on Google
2. ✅ **SEARCH** GitHub issues for the library/framework involved
3. ✅ **CHECK** Stack Overflow for similar problems
4. ✅ **BROWSE** Reddit (r/learnprogramming, r/Python, relevant subs)
5. ✅ **READ** official documentation thoroughly
6. ✅ **REVIEW** academic papers if needed
7. ✅ **ANALYZE** the root cause deeply
8. ✅ **FIX** the actual problem, not symptoms
9. ✅ **TEST** thoroughly after fixing
10. ✅ **DOCUMENT** the solution for future reference

### EXAMPLES OF FORBIDDEN BEHAVIOR:
- "This is too complex, let's use a simpler library" ❌
- "Let's just disable this feature" ❌
- "We can work around this by..." ❌
- "It's easier to rewrite this part" ❌
- "Let's use a basic implementation instead" ❌

### EXAMPLES OF CORRECT BEHAVIOR:
- "Let me search GitHub issues for this error" ✅
- "I found a similar problem on Stack Overflow, here's the fix" ✅
- "According to the documentation, we need to..." ✅
- "Research shows this is caused by X, we can fix it by Y" ✅

### THIS RULE APPLIES TO:
- Audio/speech recognition issues
- Vision/camera problems
- AI/LLM integration issues
- GUI/interface bugs
- Performance problems
- Dependency conflicts
- **ANY technical issue whatsoever**

### RATIONALE:
User has built a sophisticated, feature-rich system. Simplifying or removing features wastes the work already done. Every problem has a solution - it just needs to be researched and found.

---

## 🛡️ RULE #3: PRESERVE CODE INTEGRITY - NO BREAKING CHANGES

### FORBIDDEN ACTIONS:
- ❌ **NEVER** modify code without understanding its full impact
- ❌ **NEVER** change one part that breaks other parts
- ❌ **NEVER** remove functionality that other code depends on
- ❌ **NEVER** refactor without testing all affected areas
- ❌ **NEVER** assume changes are isolated when they're not
- ❌ **NEVER** make "quick fixes" that cause cascading failures

### REQUIRED APPROACH - BEFORE MAKING CHANGES:
1. ✅ **READ** the entire file/module being modified
2. ✅ **SEARCH** for all references to functions/classes being changed
3. ✅ **IDENTIFY** all dependencies and callers
4. ✅ **UNDERSTAND** the data flow and interactions
5. ✅ **CHECK** for imports and cross-module dependencies
6. ✅ **REVIEW** related configuration files

### REQUIRED APPROACH - WHILE MAKING CHANGES:
1. ✅ **PRESERVE** existing function signatures unless absolutely necessary
2. ✅ **MAINTAIN** backward compatibility
3. ✅ **KEEP** existing behavior for other code paths
4. ✅ **ADD** new code rather than replacing working code
5. ✅ **COMMENT** why changes are being made
6. ✅ **TEST** each change incrementally

### REQUIRED APPROACH - AFTER MAKING CHANGES:
1. ✅ **VERIFY** all callers still work correctly
2. ✅ **CHECK** that no imports are broken
3. ✅ **ENSURE** configuration is still valid
4. ✅ **TEST** the entire feature, not just the changed part
5. ✅ **VALIDATE** that other features still work

### COMMON CAUSES OF BREAKING CHANGES:
- Changing function parameters without updating all callers
- Removing imports that other code needs
- Modifying return types that other code expects
- Changing configuration keys that other code reads
- Refactoring class names without updating references
- Altering data structures that are shared across modules

### SPECIFIC AREAS REQUIRING EXTRA CARE:
- **Audio pipeline**: audio_manager.py, speechbrain_final.py, custom_model_loader.py
- **Vision system**: vision_system.py, camera integration
- **GUI**: main_window.py, settings_dialog.py
- **Configuration**: config.json, hparams files
- **Model loading**: All model inference code
- **Callbacks**: Event handlers and callback systems

### TESTING REQUIREMENTS:
- If changing audio code → test entire audio capture and recognition pipeline
- If changing vision code → test hand tracking, face detection, all vision features
- If changing GUI code → test all buttons, inputs, and displays
- If changing config → test that all config readers still work
- If changing models → test loading, inference, and output processing

### RATIONALE:
Monica AI is a complex, integrated system with many interdependent parts. Breaking one part can cascade and break multiple features. User has invested significant time building this system - it must remain functional.

---

## 📝 LAST UPDATED
December 12, 2025

## ✍️ AUTHOR
User: Marvin (Monica AI Creator)

## 🔒 ENFORCEMENT
These rules are stored in:
- This file: `CRITICAL_PROJECT_RULES.md`
- AI Memory System (3 permanent memories)
- Code enforcement in speechbrain_final.py

**ANY AI WORKING ON THIS PROJECT MUST FOLLOW THESE RULES.**
