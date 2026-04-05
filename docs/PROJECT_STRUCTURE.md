# Monica AI Project Structure

## Last Cleaned: December 7, 2025

## Main Application
```
monica_ai/                    # MAIN WORKING DIRECTORY
├── main.py                   # Entry point - RUN THIS
├── src/
│   ├── ai/                   # AI/Conversation management
│   ├── audio/                # Speech recognition, audio processing
│   ├── config/               # Configuration management
│   ├── gui/                  # Main window, settings dialog
│   ├── tts/                  # Text-to-speech (Piper TTS)
│   ├── utils/                # Utilities, world info
│   └── vision/               # Camera, vision system
├── resources/
│   └── voices/               # Piper TTS voice models
└── config.json               # Runtime configuration
```

## How to Run
```batch
RUN_MONICA.bat                # Main launcher - double-click this!
```

## Essential Knowledge Bases (DO NOT MOVE)
These files are imported by `monica_ai/src/ai/knowledge_connector.py`:
- `monica_education_k12.py`       - K-12 curriculum
- `monica_math_complete.py`       - Mathematics knowledge
- `monica_software_skills.py`     - Adobe, programming languages
- `monica_counseling_comprehensive.py` - Therapy modalities
- `monica_emotion_intelligence.py` - Emotion taxonomy
- `monica_language_teacher.py`    - 61+ world languages
- `monica_knowledge_base.py`      - General knowledge
- `monica_legal_sciences.py`      - Legal knowledge
- `monica_knowledge_2025.py`      - Current 2025 knowledge
- `monica_global_webcams.py`      - Global webcam database
- `monica_medical_knowledge.py`   - Medical knowledge
- `monica_intelligence.py`        - Intelligence/brain knowledge
- `monica_authentic_personality.py` - Personality traits

## Essential Vision Components (DO NOT MOVE)
These files are imported by `monica_ai/src/vision/vision_system.py`:
- `monica_ar_hologram_system.py`  - AR hologram effects
- `monica_video_enhancer.py`      - HDR-like video enhancement
- `monica_hand_controller.py`     - Hand gesture control
- `monica_visual_capabilities.py` - Night vision, thermal vision

## Essential GUI Components (DO NOT MOVE)
- `monica_holographic_globe_advanced.py` - 3D holographic globe

## Animation Assets
```
CSS_FOG_ANIMATION/            # Fog animation (green screen)
clouds-animation-code/        # Clouds animation (green screen)
animations/                   # Starfield, aurora animations
```

## Archive (Old/Redundant Files)
```
archive_2025_12_07/           # Archived on Dec 7, 2025
├── launchers/                # Old launcher scripts
├── old_monica_modules/       # Redundant monica_*.py files
├── old_scripts/              # Old utility scripts
├── old_windows/              # Old window_*.py files
├── old_tests/                # Old test files
├── old_docs/                 # Old documentation
└── ...                       # Other archived items
```

## External Dependencies (Large, Do Not Modify)
```
external/                     # External libraries
monica_310_env/               # Python 3.10 virtual environment
monica_fresh_env/             # Fresh virtual environment
Talk-to-Edit/                 # Talk-to-Edit model
MemMachine/                   # Memory machine
```

## Configuration Files
- `.env`                      - Environment variables
- `ollama_config.json`        - Ollama AI configuration
- `requirements.txt`          - Python dependencies
- `pytest.ini`                - Test configuration

## Database
- `monica_memory.db`          - SQLite memory database
