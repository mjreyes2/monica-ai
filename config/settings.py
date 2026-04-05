"""
Application configuration for Monica AI.
Handles all settings including audio, video, TTS, and speech recognition.
"""
import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class AppConfig:
    """Application configuration."""
    
    # Paths
    BASE_DIR: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    RESOURCES_DIR: Path = field(default=None)
    VOICES_DIR: Path = field(default=None)
    ICONS_DIR: Path = field(default=None)
    THEMES_DIR: Path = field(default=None)
    CONFIG_FILE: Path = field(default=None)
    
    # Audio Settings
    SAMPLE_RATE: int = 16000  # 16kHz (optimized for SpeechBrain)
    CHANNELS: int = 1
    CHUNK_SIZE: int = 1024
    AUDIO_FORMAT: str = "float32"
    INPUT_DEVICE_INDEX: Optional[int] = None  # USB Audio Device (1) or None for default
    INPUT_DEVICE_NAME: Optional[str] = None
    
    # Video Settings
    CAMERA_INDEX: int = 0
    CAMERA_WIDTH: int = 640
    CAMERA_HEIGHT: int = 480
    TARGET_FPS: int = 15
    
    # TTS Settings
    TTS_ENGINE: str = "piper"
    DEFAULT_VOICE_MODEL: str = "en_US-amy-medium"  # Amy - younger sounding female voice
    TTS_SPEED: float = 1.0
    TTS_PITCH: float = 1.0
    XTTS_SPEAKER_WAV: Optional[str] = None
    XTTS_CHECKPOINT: Optional[str] = None
    USE_MONICA_TTS: bool = True  # Use fine-tuned XTTS voice
    
    # Speech Recognition Settings - ONLY SPEECHBRAIN
    STT_ENGINE: str = "speechbrain"  # Use SpeechBrain for 100% accurate personal voice
    STT_LANGUAGE: str = "en"  # Set to English for better recognition
    ENERGY_THRESHOLD: float = 0.01  # Optimized for SpeechBrain
    PAUSE_THRESHOLD: float = 2.0  # Optimized for SpeechBrain
    PHRASE_TIME_LIMIT: float = 30.0  # Reasonable phrase limit
    
    # Trained model paths (personal voice model from 2500+ recorded phrases)
    PERSONAL_VOICE_MODEL_DIR: Optional[str] = None  # Set in __post_init__
    STT_TRAINING_RECORDINGS_DIR: Optional[str] = None
    TTS_TRAINING_DIR: Optional[str] = None
    TTS_FINETUNED_MODEL_DIR: Optional[str] = None
    VOICE_ADAPTATION_MODEL: Optional[str] = None
    PERSONAL_VOCABULARY: Optional[str] = None
    ENHANCED_VOICE_SIGNATURE: Optional[str] = None
    
    # Wake Word Settings
    WAKE_WORD_ENABLED: bool = True
    WAKE_WORD: str = "monica initialize"
    WAKE_WORD_SENSITIVITY: float = 0.5
    
    # UI Settings
    THEME: str = "dark"
    FONT_FAMILY: str = "Segoe UI"
    FONT_SIZE: int = 11
    WINDOW_WIDTH: int = 1280
    WINDOW_HEIGHT: int = 800
    
    # AI Backend Settings
    AI_BACKEND: str = "ollama"
    AI_MODEL: str = "llama3.2"  # Fast model that fits in 8GB VRAM
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 2048
    AI_MULTI_MODEL: bool = True  # Enable smart model routing
    
    # Spout/OBS Settings
    SPOUT_ENABLED: bool = False
    SPOUT_NAME: str = "Monica AI"
    
    def __post_init__(self):
        """Initialize paths after dataclass creation."""
        if self.RESOURCES_DIR is None:
            self.RESOURCES_DIR = self.BASE_DIR / "resources"
        if self.VOICES_DIR is None:
            self.VOICES_DIR = self.RESOURCES_DIR / "voices"
        if self.ICONS_DIR is None:
            self.ICONS_DIR = self.RESOURCES_DIR / "icons"
        if self.THEMES_DIR is None:
            self.THEMES_DIR = self.RESOURCES_DIR / "themes"
        if self.CONFIG_FILE is None:
            self.CONFIG_FILE = self.BASE_DIR / "config.json"
        
        # Ensure directories exist
        for path in [self.RESOURCES_DIR, self.VOICES_DIR, self.ICONS_DIR, self.THEMES_DIR]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Trained model paths (personal voice model from 2500+ recorded phrases)
        _pvm = self.BASE_DIR / "monica_ai" / "personal_voice_model"
        if self.PERSONAL_VOICE_MODEL_DIR is None:
            self.PERSONAL_VOICE_MODEL_DIR = str(_pvm) if _pvm.exists() else None
        if self.STT_TRAINING_RECORDINGS_DIR is None:
            _rec = self.BASE_DIR / "data" / "training" / "personal_voice_model" / "stt_training_recordings"
            self.STT_TRAINING_RECORDINGS_DIR = str(_rec) if _rec.exists() else None
        if self.TTS_TRAINING_DIR is None:
            _tts = self.BASE_DIR / "data" / "training" / "monica_tts_training"
            self.TTS_TRAINING_DIR = str(_tts) if _tts.exists() else None
        if self.TTS_FINETUNED_MODEL_DIR is None:
            _ftm = self.BASE_DIR / "data" / "training" / "monica_tts_training" / "models" / "monica_xtts_finetuned"
            self.TTS_FINETUNED_MODEL_DIR = str(_ftm) if _ftm.exists() else None
        if self.VOICE_ADAPTATION_MODEL is None:
            _vam = _pvm / "voice_adaptation_model.pt"
            self.VOICE_ADAPTATION_MODEL = str(_vam) if _vam.exists() else None
        if self.PERSONAL_VOCABULARY is None:
            _pv = _pvm / "personal_vocabulary.json"
            self.PERSONAL_VOCABULARY = str(_pv) if _pv.exists() else None
        if self.ENHANCED_VOICE_SIGNATURE is None:
            _evs = _pvm / "enhanced_voice_signature.pt"
            self.ENHANCED_VOICE_SIGNATURE = str(_evs) if _evs.exists() else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization."""
        return {
            'audio': {
                'sample_rate': self.SAMPLE_RATE,
                'channels': self.CHANNELS,
                'chunk_size': self.CHUNK_SIZE,
                'format': self.AUDIO_FORMAT,
                'input_device_index': self.INPUT_DEVICE_INDEX,
                'input_device_name': self.INPUT_DEVICE_NAME,
            },
            'video': {
                'camera_index': self.CAMERA_INDEX,
                'width': self.CAMERA_WIDTH,
                'height': self.CAMERA_HEIGHT,
                'fps': self.TARGET_FPS
            },
            'tts': {
                'engine': self.TTS_ENGINE,
                'voice_model': self.DEFAULT_VOICE_MODEL,
                'speed': self.TTS_SPEED,
                'pitch': self.TTS_PITCH
            },
            'stt': {
                'engine': self.STT_ENGINE,
                'language': self.STT_LANGUAGE,
                'energy_threshold': self.ENERGY_THRESHOLD,
                'pause_threshold': self.PAUSE_THRESHOLD,
                'phrase_time_limit': self.PHRASE_TIME_LIMIT
            },
            'wake_word': {
                'enabled': self.WAKE_WORD_ENABLED,
                'word': self.WAKE_WORD,
                'sensitivity': self.WAKE_WORD_SENSITIVITY
            },
            'ui': {
                'theme': self.THEME,
                'font_family': self.FONT_FAMILY,
                'font_size': self.FONT_SIZE,
                'window_width': self.WINDOW_WIDTH,
                'window_height': self.WINDOW_HEIGHT
            },
            'ai': {
                'backend': self.AI_BACKEND,
                'model': self.AI_MODEL,
                'temperature': self.AI_TEMPERATURE,
                'max_tokens': self.AI_MAX_TOKENS
            },
            'spout': {
                'enabled': self.SPOUT_ENABLED,
                'name': self.SPOUT_NAME
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], base_dir: Optional[Path] = None) -> 'AppConfig':
        """Create config from dictionary."""
        config = cls()
        if base_dir:
            config.BASE_DIR = base_dir
            config.__post_init__()
        
        # Audio settings
        if 'audio' in data:
            audio = data['audio']
            config.SAMPLE_RATE = int(audio.get('sample_rate', config.SAMPLE_RATE))
            config.CHANNELS = int(audio.get('channels', config.CHANNELS))
            config.CHUNK_SIZE = int(audio.get('chunk_size', config.CHUNK_SIZE))
            config.AUDIO_FORMAT = audio.get('format', config.AUDIO_FORMAT)
            config.INPUT_DEVICE_INDEX = audio.get('input_device_index', None)
            config.INPUT_DEVICE_NAME = audio.get('input_device_name', None)
        
        # Video settings
        if 'video' in data:
            video = data['video']
            config.CAMERA_INDEX = int(video.get('camera_index', config.CAMERA_INDEX))
            config.CAMERA_WIDTH = int(video.get('width', config.CAMERA_WIDTH))
            config.CAMERA_HEIGHT = int(video.get('height', config.CAMERA_HEIGHT))
            config.TARGET_FPS = int(video.get('fps', config.TARGET_FPS))
        
        # TTS settings
        if 'tts' in data:
            tts = data['tts']
            config.TTS_ENGINE = tts.get('engine', config.TTS_ENGINE)
            config.DEFAULT_VOICE_MODEL = tts.get('voice_model', config.DEFAULT_VOICE_MODEL)
            config.TTS_SPEED = float(tts.get('speed', config.TTS_SPEED))
            config.TTS_PITCH = float(tts.get('pitch', config.TTS_PITCH))
            config.XTTS_SPEAKER_WAV = tts.get('xtts_speaker_wav', getattr(config, 'XTTS_SPEAKER_WAV', None))
            config.XTTS_CHECKPOINT = tts.get('xtts_checkpoint', getattr(config, 'XTTS_CHECKPOINT', None))
            config.USE_MONICA_TTS = bool(tts.get('use_monica_tts', getattr(config, 'USE_MONICA_TTS', True)))
        
        # STT settings - ONLY SPEECHBRAIN
        if 'stt' in data:
            stt = data['stt']
            config.STT_ENGINE = stt.get('engine', config.STT_ENGINE)
            config.STT_LANGUAGE = stt.get('language', config.STT_LANGUAGE)
            config.ENERGY_THRESHOLD = float(stt.get('energy_threshold', config.ENERGY_THRESHOLD))
            config.PAUSE_THRESHOLD = float(stt.get('pause_threshold', config.PAUSE_THRESHOLD))
            config.PHRASE_TIME_LIMIT = float(stt.get('phrase_time_limit', config.PHRASE_TIME_LIMIT))
        
        # Wake word settings
        if 'wake_word' in data:
            ww = data['wake_word']
            config.WAKE_WORD_ENABLED = bool(ww.get('enabled', config.WAKE_WORD_ENABLED))
            config.WAKE_WORD = ww.get('word', config.WAKE_WORD)
            config.WAKE_WORD_SENSITIVITY = float(ww.get('sensitivity', config.WAKE_WORD_SENSITIVITY))
        
        # UI settings
        if 'ui' in data:
            ui = data['ui']
            config.THEME = ui.get('theme', config.THEME)
            config.FONT_FAMILY = ui.get('font_family', config.FONT_FAMILY)
            config.FONT_SIZE = int(ui.get('font_size', config.FONT_SIZE))
            config.WINDOW_WIDTH = int(ui.get('window_width', config.WINDOW_WIDTH))
            config.WINDOW_HEIGHT = int(ui.get('window_height', config.WINDOW_HEIGHT))
        
        # AI settings
        if 'ai' in data:
            ai = data['ai']
            config.AI_BACKEND = ai.get('backend', config.AI_BACKEND)
            config.AI_MODEL = ai.get('model', config.AI_MODEL)
            config.AI_TEMPERATURE = float(ai.get('temperature', config.AI_TEMPERATURE))
            config.AI_MAX_TOKENS = int(ai.get('max_tokens', config.AI_MAX_TOKENS))
        
        # Spout settings
        if 'spout' in data:
            spout = data['spout']
            config.SPOUT_ENABLED = bool(spout.get('enabled', config.SPOUT_ENABLED))
            config.SPOUT_NAME = spout.get('name', config.SPOUT_NAME)
        
        return config
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save config to JSON file."""
        if path is None:
            path = self.CONFIG_FILE
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=4)
        
        print(f"Configuration saved to {path}")
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> 'AppConfig':
        """Load config from JSON file."""
        base_dir = Path(__file__).parent.parent
        
        if path is None:
            path = base_dir / "config.json"
        
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return cls.from_dict(data, base_dir)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        # Return default config
        config = cls()
        config.BASE_DIR = base_dir
        config.__post_init__()
        return config


# Global config instance
config = AppConfig.load()
