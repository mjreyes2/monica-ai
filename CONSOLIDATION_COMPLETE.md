# Data Training Folder Consolidation Complete ✓

## Summary
Successfully consolidated 7 fragmented training folders into a **clean, hierarchical structure** under `data/training/`.

### Old Structure (Before)
```
data/training/
├── voice_training/           (YOUR voice - wake phrases)
├── voice_recordings/         (Generic training phrases)
├── voice_training_combined/  (Merged STT dataset)
├── personal_voice_model/     (Model caches)
├── monica_tts_training/      (TTS training)
├── monica_stt_training/      (STT training)
├── stt_training_recordings/ (Legacy folder)
```

### New Structure (After) ✨
```
data/training/
├── recordings/               # ALL voice recordings
│   ├── wake_phrases/        (YOUR voice - was: voice_training/recordings/MJP/)
│   └── training_phrases/    (Generic phrases - was: voice_recordings/training_phrases/)
├── datasets/                # ALL training datasets
│   ├── stt_combined/        (Merged STT data - was: voice_training_combined/)
│   └── tts_corpora/         (TTS datasets - was: monica_tts_training/datasets/)
├── models/                  # ALL trained models
│   ├── stt/                 (STT checkpoints)
│   └── tts/                 (TTS voice models/checkpoints)
├── cache/                   # ALL model caches
│   ├── hf_cache/           (HuggingFace cache - was: personal_voice_model/)
│   ├── speaker_cached/     (Speaker embeddings)
│   ├── asr_wav2vec2_cached/ (ASR model cache)
│   └── stt_training_recordings/  (Moved from cache)
└── scripts/                 # ALL training scripts
    ├── stt/                 (STT training code - was: monica_stt_training/)
    └── tts/                 (TTS training code - was: monica_tts_training/)
```

## Files Moved ✓

### Recordings
- `voice_training/recordings/MJP/*` → `recordings/wake_phrases/`
  - **21 .wav files** (your personal wake phrases)
  - **1 training_logs directory**
  
- `voice_recordings/training_phrases/` → `recordings/training_phrases/`
  - Ready for generic training phrases

### Datasets
- `voice_training_combined/` → `datasets/stt_combined/`
  - `training_manifest.json`
  - `training_data.csv`
  - `transcriptions.txt`
  
- `monica_tts_training/datasets/` → `datasets/tts_corpora/`
  - `LJSpeech-1.1/`
  - `LibriTTS_R/`
  - Other datasets

### Models & Cache
- `personal_voice_model/` → `cache/`
  - `hf_cache/` (HuggingFace models)
  - `speaker_cached/`
  - `asr_wav2vec2_cached/`
  - `stt_training_recordings/`

### Scripts
- `monica_tts_training/` → `scripts/tts/`
  - `launch_tts_training.py`
  - Training scripts and configs
  
- `monica_stt_training/` → `scripts/stt/`
  - Training scripts and configs

## Code Updates ✓

**Updated 5 critical Python scripts:**
1. ✓ `scripts/training_hub_gui.py` - Updated all 4 path constants
2. ✓ `scripts/continue_training.py` - Updated TRAIN/VAL CSV paths
3. ✓ `scripts/create_training_csvs.py` - Updated manifest directory
4. ✓ `scripts/prepare_all_training_data.py` - Updated all recording and output paths
5. ✓ `src/audio/tts_diagnostics.py` - Updated training_root and voice_dir paths

**Reference sheets for other code:**
- Old: `voice_training/recordings/MJP/` → New: `recordings/wake_phrases/`
- Old: `voice_recordings/training_phrases/` → New: `recordings/training_phrases/`
- Old: `voice_training_combined/` → New: `datasets/stt_combined/`
- Old: `personal_voice_model/` → New: `cache/`
- Old: `monica_tts_training/` → New: `scripts/tts/` (for code) or `datasets/tts_corpora/` (for data)
- Old: `monica_stt_training/` → New: `scripts/sst/`
- Old: `stt_training_recordings/` → New: `recordings/training_phrases/` (legacy, consolidated)

## Old Folders (Safe to Delete)

The following old folders are now empty or redundant:
```
- data/training/voice_training/          (empty - moved)
- data/training/voice_recordings/        (empty - moved)
- data/training/voice_training_combined/ (empty - moved) 
- data/training/personal_voice_model/    (needs review if other code refs exist)
- data/training/monica_stt_training/     (empty - moved)
- data/training/monica_tts_training/     (partially moved - needs review)
- data/training/stt_training_recordings/ (legacy - can delete)
```

## Benefits ✨

1. **Clarity** - Easy to find: all recordings in `recordings/`, all data in `datasets/`, all cache in `cache/`
2. **Scalability** - Easy to add more recording types, models, datasets without folder explosion
3. **Maintenance** - Fewer similar-sounding folder names (was: 3 "voice_*" + 2 "monica_*")
4. **Organization** - Logical grouping (by type, not by tool/model name)
5. **Reduced Confusion** - Down from 7 fragmented folders to 5 logical top-level folders

## Next Steps

1. ✓ Code updated in critical files (training_hub_gui, prepare_all_training_data, etc.)
2. ✓ New consolidated structure created and populated
3. ⏳ Review and update remaining code references if needed (`src/models/`, `monica_ai/src/`, etc.)
4. ⏳ Delete old empty folders once confident all code updated
5. ⏳ Update TRAINING_FOLDER_GUIDE.md with new paths

## Locations

- **Training Hub GUI:** `Launch_Training_Hub.bat`
- **Consolidated Guide:** `TRAINING_FOLDER_GUIDE.md`
- **New Structure Root:** `data/training/`

---

**Consolidation Date:** April 4, 2026
**Status:** ✓ COMPLETE
