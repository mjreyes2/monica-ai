# organize_monica.py
import os
import shutil
from pathlib import Path

file_map = {
    'src/core/': [
        'monica.py',
        'monica_services_launcher.py',
        'monica_ar_core.py',
        'monica_orb_window.py'
    ],
    'src/services/': [
        'monica_consciousness.py',
        'monica_knowledge_base.py',
        'monica_research_system.py',
        'monica_satellite_data.py',
        'monica_map_navigation.py'
    ],
    'src/models/': [
        'monica_train_wav2vec.py',
        'train_feminine_voice.py',
        'train_wav2vec2_final.py',
        'train_xtts_feminine_official.py',
        'prepare_training_data.py'
    ],
    'src/ui/': [
        'monica_globe_window.py',
        'monica_realistic_globe.py',
        'monica_video_enhancer.py',
        'opencv_window_manager.py',
        'tkinter_ar_windows.py'
    ],
    'src/utils/': [
        'monica_audio_manager.py',
        'MonicaKnowledgeManager.py',
        'monitor_gpu_memory.py'
    ],
    'data/': [
        'monica_memory.db'
    ],
    'data/training/': [
        'phrases.txt',
        'stt_training_phrases.txt',
        'training_text.txt'
    ],
    'config/': [
        'ollama_config.json'
    ],
    'scripts/': [
        'START_VOICE_TRAINING.bat',
        'setup_enhanced_stt.bat',
        'setup_feminine_voice.py'
    ],
    'tests/': [
        'pytest.ini'
    ],
    'logs/': [
        'monica_services.log',
        'training_log.txt'
    ]
}

for target_dir, files in file_map.items():
    os.makedirs(target_dir, exist_ok=True)
    for file in files:
        if os.path.exists(file):
            shutil.move(file, os.path.join(target_dir, file))

# Move all test files
for file in Path('.').glob('test_*.py'):
    shutil.move(str(file), 'tests/')

# Move all markdown files
for file in Path('.').glob('*.md'):
    shutil.move(str(file), 'docs/')
