# config/config.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
LOG_DIR = BASE_DIR / 'logs'
MODEL_DIR = DATA_DIR / 'models'

# Database paths
MEMORY_DB = DATA_DIR / 'monica_memory.db'

# Model paths
STT_MODEL_PATH = MODEL_DIR / 'stt'
TTS_MODEL_PATH = MODEL_DIR / 'tts'

# Training data paths
TRAINING_DATA_DIR = DATA_DIR / 'training'
PHRASES_FILE = TRAINING_DATA_DIR / 'phrases.txt'

# Service configuration
OLLAMA_CONFIG = BASE_DIR / 'config' / 'ollama_config.json'