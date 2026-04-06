# Monica Training Folder Organization Guide

## Overview
Your project contains 6 interconnected training folders plus 3 phrase corpus files. This guide explains what each folder is for and how they work together.

---

## Training Folder Structure

The training data and scripts are now organized under `data/training/` in a clear, hierarchical structure:

### 1. `data/training/recordings/wake_phrases/`
**Purpose:** YOUR PERSONAL WAKE PHRASE RECORDINGS

- **Location:** `data/training/recordings/wake_phrases/`
- **File Format:** WAV format, 16,000 Hz sample rate
- **Naming Convention:** `phrase_NNNNN_description.wav` (e.g., `phrase_00001_hello_monica.wav`)
- **What Goes Here:** Wake words and activation phrases specific to YOUR voice
- **Usage:** Used to create a **personal voice model** that recognizes when YOU speak the wake word
- **Best Practice:** Record 50+ samples with different inflections and background noise levels

**Example Files:**
```
phrase_00001_hello_monica.wav
phrase_00002_monica_please.wav
phrase_00003_hey_monica.wav
```

### 2. `data/training/recordings/training_phrases/`
**Purpose:** GENERIC TRAINING SENTENCES (NOT personalized)

- **Location:** `data/training/recordings/training_phrases/`
- **File Format:** WAV format, 16,000 Hz sample rate
- **Naming Convention:** `NNNN_description.wav` (e.g., `0001_the_quick_brown_fox.wav`)
- **What Goes Here:** Standard sentences for general STT improvement
- **Usage:** Improves Monica's ability to transcribe ANY voice, not just yours
- **Context:** These are common English sentences (novels, textbooks, standard training data)
- **Best Practice:** Use sentences from diverse domains (tech, literature, everyday speech)

**Example Files:**
```
0001_the_quick_brown_fox.wav
0002_speech_recognition_technology.wav
0003_natural_language_processing.wav
```

### 3. `data/training/datasets/stt_combined/`
**Purpose:** UNIFIED STT TRAINING DATASET (combines wake_phrases + training_phrases)

- **Location:** `data/training/datasets/stt_combined/`
- **What It Does:** This folder is created by `scripts/prepare_all_training_data.py`
- **Contents:** Merges YOUR wake phrases + generic training phrases into one dataset
- **File Structure:**
  ```
  stt_combined/
  ├── training_manifest.json    # Maps audio files to transcriptions
  ├── training_data.csv         # Train/val split (90/10)
  ├── transcriptions.txt        # All text labels
  └── training_hub_state.json   # GUI state tracking
  ```
- **Usage:** Fed into STT training scripts as the primary dataset
- **Note:** Regenerated each time you click "1) Prepare STT Dataset" in the Training Hub

### 4. `data/training/cache/`
**Purpose:** CACHED MODELS AND EMBEDDINGS (HuggingFace, Nemo, SpeechBrain)

- **Location:** `data/training/cache/`
- **Subdirectories:**
  - `hf_cache/` → HuggingFace model cache
  - `nemo_cache/` → Nemo cache
  - `speechbrain_cache/` → SpeechBrain model cache
- **What It Does:** Stores model weights and embeddings to speed up training and inference
- **Auto-Managed:** You don't need to touch this; it's created automatically
- **Size:** Can grow large (~500 MB+) as models are cached
- **Cleanup:** Safe to delete if you run out of space (will be recreated on next training)

### 5. `data/training/scripts/tts/`
**Purpose:** TEXT-TO-SPEECH (TTS) TRAINING SCRIPTS

- **Location:** `data/training/scripts/tts/`
- **Main Files:**
  - `launch_tts_training.py` → Launcher for TTS training
  - `train_monica_tts.py` → TTS training script
  - `hparams_monica.yaml` → TTS hyperparameters
- **What It Does:** Contains scripts for training Monica's voice synthesis (TTS)
- **Usage:** Click "3) Launch TTS Training" in the Training Hub

### 6. `data/training/scripts/stt/`
**Purpose:** SPEECH-TO-TEXT (STT) TRAINING SCRIPTS

- **Location:** `data/training/scripts/stt/`
- **Main Files:**
  - `train_stt_combined.py` → Main STT trainer
  - `hparams_monica.yaml` → STT hyperparameters
  - `recorded_phrases.json` → List of phrase metadata
- **What It Does:** Contains scripts for training Monica's speech recognition (STT)
- **Usage:** Called by "2) Continue STT Training" button

---

## Phrase Files

### File 1: **phrases.txt** (1,683 lines)
**Purpose:** Common proverbs and idioms for vocabulary

**Sample Content:**
```
The quick brown fox jumps over the lazy dog
A journey of a thousand miles begins with a single step
To be or not to be that is the question
All that glitters is not gold
Actions speak louder than words
```

**Use Case:** General vocabulary training, helps STT recognize common expressions

### File 2: **training_text.txt** (1,000 lines)
**Purpose:** Technical and AI-focused phrases

**Sample Content:**
```
THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG
SPEECH RECOGNITION TECHNOLOGY HAS IMPROVED SIGNIFICANTLY
NATURAL LANGUAGE PROCESSING ENABLES BETTER UNDERSTANDING
MACHINE LEARNING MODELS CAN TRANSCRIBE AUDIO ACCURATELY
ACOUSTIC MODELS CONVERT SOUND WAVES TO TEXT
```

**Use Case:** Domain-specific vocabulary for voice assistant context

### File 3: **stt_training_phrases.txt** (38,882 lines)
**Purpose:** Large corpus of text extracted from English grammar and linguistics textbooks

**Content:** Complete sentences used for language modeling

**Use Case:** Large general corpus to improve transcription quality across diverse English

### File 4: **PHRASES_MASTER.txt** (40,505 unique lines) ⭐ NEW
**Purpose:** CONSOLIDATED MASTER PHRASE FILE (combines all above + deduplication)

**Statistics:**
- Total phrases consolidated: 41,565 (before deduplication)
- Unique phrases: 40,505 (after deduplication)
- File size: 3.3 MB

**Location:** `data/training/PHRASES_MASTER.txt`

**Use Case:** Single reference file for all training phrases; use if you need one comprehensive vocabulary corpus

**How It Was Created:**
```
phrases.txt (1,683) 
    + training_text.txt (1,000) 
    + stt_training_phrases.txt (38,882)
    = 41,565 total
    → DEDUPLICATED → 40,505 unique
```

---

## Data Flow Diagram

```
YOUR WAKE PHRASES              GENERIC TRAINING PHRASES
│                              │
├─ data/training/recordings/wake_phrases/  data/training/recordings/training_phrases/
│  (phrase_NNNNN_*.wav)           (NNNN_*.wav)
│                                 │
└──────────────┬──────────────────┘
               │
          PREPARE DATASET
               │
    scripts/prepare_all_training_data.py
               │
               ▼
    data/training/datasets/stt_combined/
    ├─ training_manifest.json
    ├─ training_data.csv (90/10 split)
    └─ transcriptions.txt
               │
         ┌─────┴─────┐
         │           │
         ▼           ▼
  STT TRAINING   TTS TRAINING
    (Continue)     (Launch)
         │           │
         ▼           ▼
  data/training/cache/  data/training/scripts/tts/
      (models)            (tts scripts)
```

---

## Recommended Workflow

### Step 1: Record New Phrases
```
1. Record your wake words → data/training/recordings/wake_phrases/
   - Use format: phrase_NNNNN_description.wav
   - Target: 50+ recordings with variation

2. Record generic sentences → data/training/recordings/training_phrases/
   - Use format: NNNN_description.wav
   - Target: Mix of technical, everyday, literature
```

### Step 2: Use Training Hub GUI
```
Launch: Launch_Training_Hub.bat

1. Click "Refresh Scan"
   → Shows count of files in both folders
   → Detects invalid filenames

2. Click "Auto-Rename Invalid Filenames"
   → Fixes any naming convention mismatches
   → Prepares data for training

3. Click "1) Prepare STT Dataset"
   → Consolidates into data/training/datasets/stt_combined/
   → Creates training_manifest.json & CSV

4. Click "2) Continue STT Training"
   → Trains wav2vec2 on YOUR voice + phrases
   → Improves word error rate (WER)

5. Click "3) Launch TTS Training"
   → Trains voice synthesis model
   → Makes Monica sound closer to your recording
```

### Step 3: Monitor Profile
- Click "Profile Inspector" tab in Training Hub
- See what Monica has remembered about you
- Check mood history, relationships learned, custom facts

---

## Summary: What What's For

| Folder | Purpose | You Add | Monica Uses |
|--------|---------|---------|-------------|
| **data/training/recordings/wake_phrases/** | YOUR wake words | 50+ .wav files | Personal voice model |
| **data/training/recordings/training_phrases/** | Generic sentences | 100+ .wav files | General STT accuracy |
| **data/training/datasets/stt_combined/** | Unified dataset | (Auto-merged) | STT training input |
| **data/training/cache/** | Model cache | (Auto-created) | Inference speedup |
| **data/training/scripts/tts/** | TTS training scripts | (Code only) | TTS voice output |
| **data/training/scripts/stt/** | STT training scripts | (Code only) | STT model training |

---

## Quick Reference: File Naming

### Wake Phrase Format
```
phrase_NNNNN_slug.wav

Examples:
✓ phrase_00001_hello_monica.wav
✓ phrase_00002_monica_activate.wav
✓ phrase_00003_hey_monica.wav
✗ hello_monica.wav            (WRONG)
✗ 1_hello.wav                 (WRONG)
```

### General Phrase Format
```
NNNN_slug.wav

Examples:
✓ 0001_the_quick_brown_fox.wav
✓ 0100_weather_forecast.wav
✓ 0500_machine_learning.wav
✗ the_quick_brown_fox.wav     (WRONG)
✗ phrase_00001_fox.wav        (WRONG - this is for wake phrases!)
```

---

## Troubleshooting

Q: Why are there two recording folders?
A: `data/training/recordings/wake_phrases/` is YOUR voice (custom model), `data/training/recordings/training_phrases/` is generic data (general accuracy)

**Q: Can I delete `stt_training_recordings/`?**
A: Yes, after verifying your important recordings are backed up elsewhere.

**Q: What if files don't auto-rename?**
A: Manually rename using the pattern above, or check permissions on the folder.

**Q: How often should I retrain?**
A: Every 50-100 new recordings. Click buttons in order: Prepare → Train STT → Train TTS

**Q: Can I use PHRASES_MASTER.txt directly?**
A: Yes! It's a unified corpus if you need a single phrase file for other tools.

---

## Files Modified/Created

✅ **Updated:** `scripts/training_hub_gui.py`
- Added "Profile Inspector" tab
- Shows decrypted user profile (name, mood, relationships, etc.)
- Can export profile to JSON

✅ **Created:** `data/training/PHRASES_MASTER.txt`
- Consolidated all 3 phrase files
- 40,505 unique phrases
- 3.3 MB corpus ready for use

---

**Last Updated:** April 4, 2026
**Monica Project Directory:** c:\Users\Marvi\OneDrive\monica_project
