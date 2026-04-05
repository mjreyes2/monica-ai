"""
Coqui TTS Integration for Monica AI.
High-quality neural text-to-speech with multiple voices and emotions.
"""
import numpy as np
import threading
import time
from typing import Optional, Callable, List
from pathlib import Path

# Lazy load TTS
_tts_model = None


def _load_coqui_tts(model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"):
    """Load Coqui TTS model."""
    global _tts_model
    if _tts_model is None:
        try:
            from TTS.api import TTS
            print(f"[COQUI TTS] Loading model: {model_name}")
            _tts_model = TTS(model_name=model_name, progress_bar=True)
            print("[COQUI TTS] Model loaded successfully")
        except Exception as e:
            print(f"[COQUI TTS] Error loading model: {e}")
            _tts_model = None
    return _tts_model


class CoquiTTSManager:
    """
    Coqui TTS Manager for high-quality speech synthesis.
    
    Features:
    - Multiple voice models
    - Emotion control (with some models)
    - Multi-speaker support
    - High quality neural TTS
    """
    
    # Available models (subset of most useful)
    MODELS = {
        'ljspeech': 'tts_models/en/ljspeech/tacotron2-DDC',
        'vctk': 'tts_models/en/vctk/vits',  # Multi-speaker
        'jenny': 'tts_models/en/jenny/jenny',  # Natural female voice
        'fast': 'tts_models/en/ljspeech/fast_pitch',  # Faster
    }
    
    def __init__(
        self,
        model_name: str = "jenny",
        sample_rate: int = 22050,
        speaker: Optional[str] = None
    ):
        """Initialize Coqui TTS."""
        self.model_name = model_name
        self.sample_rate = sample_rate
        self.speaker = speaker
        
        # State
        self.tts = None
        self.is_initialized = False
        self.is_speaking = False
        self.stop_event = threading.Event()
        
        # Callbacks
        self.start_callbacks: List[Callable[[str], None]] = []
        self.end_callbacks: List[Callable[[str], None]] = []
        
        print(f"[COQUI TTS] Manager created (model: {model_name})")
    
    def initialize(self) -> bool:
        """Initialize the TTS engine."""
        if self.is_initialized:
            return True
        
        try:
            model_path = self.MODELS.get(self.model_name, self.model_name)
            self.tts = _load_coqui_tts(model_path)
            
            if self.tts is not None:
                self.is_initialized = True
                
                # Get sample rate from model
                if hasattr(self.tts, 'synthesizer') and self.tts.synthesizer:
                    self.sample_rate = self.tts.synthesizer.output_sample_rate
                
                print(f"[COQUI TTS] Initialized at {self.sample_rate}Hz")
                return True
            
            return False
            
        except Exception as e:
            print(f"[COQUI TTS] Initialization error: {e}")
            return False
    
    def speak(self, text: str, block: bool = True) -> Optional[np.ndarray]:
        """Synthesize and play speech."""
        if not self.is_initialized:
            if not self.initialize():
                return None
        
        if not text.strip():
            return None
        
        # Clean text
        text = self._clean_text(text)
        
        self.stop_event.clear()
        self.is_speaking = True
        
        # Notify start
        for callback in self.start_callbacks:
            try:
                callback(text)
            except:
                pass
        
        try:
            # Synthesize
            print(f"[COQUI TTS] Synthesizing: {text[:50]}...")
            
            wav = self.tts.tts(
                text=text,
                speaker=self.speaker,
            )
            
            # Convert to numpy array
            audio_data = np.array(wav, dtype=np.float32)
            
            print(f"[COQUI TTS] Synthesized {len(audio_data)} samples")
            
            if block:
                self._play_audio(audio_data)
            
            return audio_data
            
        except Exception as e:
            print(f"[COQUI TTS] Synthesis error: {e}")
            return None
        finally:
            self.is_speaking = False
            
            # Notify end
            for callback in self.end_callbacks:
                try:
                    callback(text)
                except:
                    pass
    
    def _play_audio(self, audio_data: np.ndarray):
        """Play synthesized audio."""
        try:
            import sounddevice as sd
            
            print(f"[COQUI TTS] Playing audio at {self.sample_rate}Hz")
            sd.play(audio_data, samplerate=self.sample_rate)
            
            # Wait with interrupt checking
            duration = len(audio_data) / self.sample_rate
            elapsed = 0
            check_interval = 0.05
            
            while elapsed < duration and not self.stop_event.is_set():
                time.sleep(check_interval)
                elapsed += check_interval
            
            if self.stop_event.is_set():
                sd.stop()
                print("[COQUI TTS] Playback interrupted")
            else:
                sd.wait()
                print("[COQUI TTS] Playback complete")
                
        except Exception as e:
            print(f"[COQUI TTS] Playback error: {e}")
    
    def _clean_text(self, text: str) -> str:
        """Clean text for synthesis."""
        import re
        
        # Remove asterisk expressions
        text = re.sub(r'\*[^*]+\*', '', text)
        
        # Remove markdown
        text = re.sub(r'[*_#`]', '', text)
        
        # Clean up whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def stop(self):
        """Stop current speech."""
        self.stop_event.set()
        self.is_speaking = False
        
        try:
            import sounddevice as sd
            sd.stop()
        except:
            pass
    
    def register_start_callback(self, callback: Callable[[str], None]):
        """Register callback for speech start."""
        if callback not in self.start_callbacks:
            self.start_callbacks.append(callback)
    
    def register_end_callback(self, callback: Callable[[str], None]):
        """Register callback for speech end."""
        if callback not in self.end_callbacks:
            self.end_callbacks.append(callback)
    
    def get_available_speakers(self) -> List[str]:
        """Get available speakers for multi-speaker models."""
        if not self.is_initialized:
            return []
        
        try:
            if hasattr(self.tts, 'speakers') and self.tts.speakers:
                return self.tts.speakers
        except:
            pass
        
        return []
    
    def set_speaker(self, speaker: str):
        """Set the speaker for multi-speaker models."""
        self.speaker = speaker


# Test function
def test_coqui():
    """Test Coqui TTS."""
    tts = CoquiTTSManager(model_name="jenny")
    tts.speak("Hello! I am Monica, your AI assistant. How can I help you today?")


if __name__ == "__main__":
    test_coqui()
