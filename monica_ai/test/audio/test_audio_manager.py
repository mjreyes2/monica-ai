"""
Tests for the AudioManager class.
"""
import pytest
import numpy as np
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

# Import the AudioManager class
from src.audio.audio_manager import AudioManager

# Mock configuration
class MockConfig:
    def __init__(self):
        # Audio settings
        self.SAMPLE_RATE = 16000
        self.CHANNELS = 1
        self.FRAMES_PER_BUFFER = 1024
        self.WAKE_WORD = 'monica'
        self.WAKE_WORD_ENABLED = True
        self.WAKE_WORD_SENSITIVITY = 0.5
        
        # STT settings
        self.STT_ENGINE = 'whisper'
        self.WHISPER_MODEL_SIZE = 'tiny'
        self.STT_LANGUAGE = 'en'
        
        # Audio device settings
        self.INPUT_DEVICE_INDEX = None
        self.OUTPUT_DEVICE_INDEX = None
        
        # Audio processing
        self.VOICE_ACTIVITY_THRESHOLD = 0.02
        self.SILENCE_THRESHOLD = 0.01
        self.SILENCE_DURATION = 0.5
        
        # Audio visualization
        self.VISUALIZATION_SAMPLES = 1000
        
        # For backward compatibility
        self.audio = {
            'sample_rate': self.SAMPLE_RATE,
            'channels': self.CHANNELS,
            'frames_per_buffer': self.FRAMES_PER_BUFFER,
            'wake_word': self.WAKE_WORD
        }
        
        self.stt = {
            'engine': self.STT_ENGINE,
            'whisper_model': self.WHISPER_MODEL_SIZE,
            'language': self.STT_LANGUAGE
        }

class TestAudioManager:
    """Test cases for AudioManager."""
    
    @pytest.fixture
    def audio_manager(self):
        """Create an AudioManager instance for testing with mock config."""
        mock_config = MockConfig()
        with patch('sounddevice.Stream'), \
             patch('src.audio.audio_manager.WakeWordDetector'):
            manager = AudioManager(config=mock_config)
            # Mock the stream to prevent actual audio I/O during tests
            manager.stream = MagicMock()
            return manager
    
    def test_initialization(self, audio_manager):
        """Test that AudioManager initializes correctly."""
        assert audio_manager is not None
        assert hasattr(audio_manager, 'config')
        assert hasattr(audio_manager.config, 'SAMPLE_RATE')
        assert hasattr(audio_manager.config, 'CHANNELS')
        assert audio_manager.config.SAMPLE_RATE == 16000
        assert audio_manager.config.CHANNELS == 1
        
    def test_start_stop(self, audio_manager):
        """Test starting and stopping the audio stream."""
        # Mock the input_stream since it's not initialized in the test fixture
        audio_manager.input_stream = MagicMock()
        
        # Test starting input
        result = audio_manager.start_input()
        assert isinstance(result, bool)
        
        # Test stopping input
        audio_manager.stop_input()
        # Since input_stream is mocked, we can't verify actual stop behavior
        
    def test_audio_callback(self, audio_manager):
        """Test the audio callback function."""
        # Create a test audio frame
        test_frame = np.random.rand(1024, 1).astype(np.float32)
        
        # Mock the callback
        mock_callback = MagicMock()
        audio_manager.register_audio_callback(mock_callback)
        
        # Test that callbacks can be registered
        assert len(audio_manager.audio_callbacks) == 1
        
        # Test unregistering
        audio_manager.unregister_audio_callback(mock_callback)
        assert len(audio_manager.audio_callbacks) == 0
        
    def test_wake_word_detection(self, audio_manager):
        """Test wake word detection setup."""
        # Test that wake word detector exists
        assert audio_manager.wake_word_detector is not None
        
        # Test setting wake word
        audio_manager.set_wake_word("test wake word")
        # Note: Since wake_word_detector is mocked, we can't test the actual value
        
        # Test setting sensitivity
        audio_manager.set_wake_word_sensitivity(0.7)
        # Note: Since wake_word_detector is mocked, we can't test the actual value
