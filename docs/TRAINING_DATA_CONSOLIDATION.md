# Monica AI - Training Data Consolidation Report

## STT Training Data

### Primary Locations (ACTIVE - used by the system)
- **`monica_ai/personal_voice_model/`** - The main personal voice model directory
  - `voice_adaptation_model.pt` (160 MB) - Trained voice adaptation weights
  - `personal_vocabulary.json` (96 KB) - Personal vocabulary for better recognition
  - `enhanced_voice_signature.pt` (3 KB) - Voice signature for speaker ID
  - `vocabulary.txt` - Text vocabulary
  - `test_results.json` - Model test results
  - Various cached models: `asr_cached/`, `asr_wav2vec2_cached/`, `hf_cache/`, `speaker_cached/`

- **`data/training/personal_voice_model/stt_training_recordings/`** (6375 items)
  - ~3187 phrase pairs (WAV + text) - Main STT training recordings
  - This is the PRIMARY recording dataset used for training

- **`data/training/voice_training_combined/`** (11 items)
  - Combined training dataset with `train.json`, `val.json`, `vocab.json`
  - Pre-processed dataset ready for training

### Secondary/Legacy Locations
- **`data/training/voice_training/recordings/`** (4239 items)
  - Older voice training recordings (MJP speaker)
  - May overlap with personal_voice_model recordings

- **`data/training/monica_stt_training/`** (31959 items)
  - STT training data, phrases, and model outputs

- **`monica_ai/voice_training/recordings/MJP/`** (7 items)
  - Small set of early test recordings

### Empty/Unused Locations (safe to remove)
- **`stt_friend_package/stt_training_recordings/`** (0 items) - Empty
- **`data/training/voice_recordings/`** (0 items) - Empty
- **`monica_ai/personal_voice_model/temp/`** (0 items) - Empty
- **`monica_ai/personal_voice_model/hf_cache/`** (0 items inside nested dirs) - May contain cached models

## TTS Training Data

### Primary Locations (ACTIVE)
- **`data/training/monica_tts_training/`** (127155 items)
  - `models/monica_xtts_finetuned/` (28 items) - Fine-tuned XTTS model
  - `models/xtts_official_trained/` (27 items) - Official trained model
  - `models/monica_enhanced_voice/` - Enhanced voice model
  - `models/monica_quantum_voice/` - Quantum voice model
  - `output/` - Generated speech samples (21 WAV files)

### Empty TTS Model Dirs
- `data/training/monica_tts_training/models/xtts_full_finetuned/` (0 items)
- `data/training/monica_tts_training/models/xtts_weights_trained/` (0 items)

## Training Scripts

### Duplicate Scripts (IDENTICAL)
- `stt_friend_package/record_stt_training.py` == `scripts/audio/record_stt_training.py`
  - **Action**: Keep `scripts/audio/record_stt_training.py`, the stt_friend_package copy is redundant

### Training Script Locations
| Location | Purpose | Count |
|----------|---------|-------|
| `scripts/` | Top-level training launchers and utilities | 9 scripts |
| `scripts/audio/` | Audio recording for STT training | 1 script |
| `monica_ai/voice_training/` | SpeechBrain/NeMo training and finetuning | 11 scripts |
| `src/models/` | wav2vec2, XTTS, language model training | 10 scripts |
| `data/training/monica_tts_training/` | XTTS finetuning scripts | 5 scripts |
| `data/training/monica_stt_training/` | STT combined finetuning | 1 script |

### Key Training Scripts
- **STT Recording GUI**: `monica_ai/voice_training/record_voice.py` (254 KB - main GUI)
- **STT Training**: `monica_ai/voice_training/train_speechbrain_wrapper.py` (main trainer)
- **TTS Fine-tuning**: `data/training/monica_tts_training/finetune_xtts_full.py`
- **Launch GUI**: `scripts/launch_voice_training_gui.py` (launcher for record_voice.py)

## Service Integration

### STT Service (`src/services/stt_service.py`)
- **Primary**: Custom-trained `FinalSpeechBrainRecognizer` from `monica_ai/src/audio/speechbrain_final.py`
  - Uses `voice_adaptation_model.pt` from `monica_ai/personal_voice_model/`
  - Uses `personal_vocabulary.json` for vocabulary boost
  - Uses `enhanced_voice_signature.pt` for speaker identification
- **Fallback 1**: Standard SpeechBrain `asr-wav2vec2-commonvoice-en`
- **Fallback 2**: Whisper
- **Fallback 3**: Google Speech Recognition

### TTS Service (`src/audio/tts_manager.py`)
- **Primary**: MonicaTTS (XTTS with trained voice from `data/training/monica_tts_training/models/`)
- **Fallback 1**: Piper TTS
- **Fallback 2**: Coqui TTS
- **Fallback 3**: pyttsx3 system TTS

## Config Integration (`config/settings.py`)
All training paths are auto-detected in `__post_init__`:
- `PERSONAL_VOICE_MODEL_DIR` -> `monica_ai/personal_voice_model/`
- `STT_TRAINING_RECORDINGS_DIR` -> `data/training/personal_voice_model/stt_training_recordings/`
- `TTS_TRAINING_DIR` -> `data/training/monica_tts_training/`
- `TTS_FINETUNED_MODEL_DIR` -> `data/training/monica_tts_training/models/monica_xtts_finetuned/`
- `VOICE_ADAPTATION_MODEL` -> `monica_ai/personal_voice_model/voice_adaptation_model.pt`
- `PERSONAL_VOCABULARY` -> `monica_ai/personal_voice_model/personal_vocabulary.json`
- `ENHANCED_VOICE_SIGNATURE` -> `monica_ai/personal_voice_model/enhanced_voice_signature.pt`

## Microphone Selection
- Available in GUI via dropdown (`src/services/gui_service.py`)
- `STTService.list_microphones()` enumerates available input devices
- `STTService.set_microphone()` changes device at runtime
- Config: `INPUT_DEVICE_INDEX` and `INPUT_DEVICE_NAME` in `config/settings.py`
