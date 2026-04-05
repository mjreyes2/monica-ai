"""
Vosk Speech-to-Text Integration for Monica AI

Fast, accurate, offline speech recognition using Vosk.
- No API keys needed
- Works offline
- Trainable/customizable
- Low memory footprint
- Fast startup
"""

import os
import json
import threading
import queue
import numpy as np
from typing import Callable, List, Optional
from pathlib import Path

# Try to import Vosk
try:
    from vosk import Model, KaldiRecognizer, SetLogLevel
    HAS_VOSK = True
    SetLogLevel(-1)  # Suppress Vosk logs
except ImportError:
    HAS_VOSK = False
    print("[VOSK] Vosk not installed. Run: pip install vosk")

# Try to import sounddevice for microphone
try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False
    print("[VOSK] sounddevice not installed. Run: pip install sounddevice")


class VoskSTT:
    """
    Vosk Speech-to-Text wrapper.
    Fast, offline speech recognition.
    """
    
    # Model URLs for download
    MODELS = {
        "small": "vosk-model-small-en-us-0.15",  # ~40MB, fast
        "medium": "vosk-model-en-us-0.22",       # ~1.8GB, accurate
        "large": "vosk-model-en-us-0.22-lgraph", # ~128MB, good balance
    }
    
    def __init__(self, model_path: str = None, model_size: str = "small"):
        """
        Initialize Vosk STT.
        
        Args:
            model_path: Path to Vosk model directory
            model_size: Model size (small, medium, large)
        """
        self.model = None
        self.recognizer = None
        self.is_listening = False
        self.callbacks: List[Callable[[str], None]] = []
        self.listen_thread = None
        self.stop_event = threading.Event()
        self.audio_queue = queue.Queue()
        
        # Audio settings
        self.sample_rate = 16000
        self.device_index = None
        
        if not HAS_VOSK:
            print("[VOSK] [ERROR] Vosk not available")
            return
        
        # Find or download model
        self.model_path = self._get_model_path(model_path, model_size)
        
        if self.model_path and os.path.exists(self.model_path):
            try:
                print(f"[VOSK] Loading model from {self.model_path}...")
                self.model = Model(self.model_path)
                self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
                self.recognizer.SetWords(True)  # Enable word-level timestamps
                print("[VOSK] [OK] Model loaded successfully!")
            except Exception as e:
                print(f"[VOSK] [ERROR] Failed to load model: {e}")
        else:
            print(f"[VOSK] [ERROR] Model not found at {self.model_path}")
            print("[VOSK] Download a model from: https://alphacephei.com/vosk/models")
            print(f"[VOSK] Extract to: {self._get_default_model_dir()}")
    
    def _get_model_path(self, model_path: str, model_size: str) -> str:
        """Get the model path, checking various locations."""
        if model_path and os.path.exists(model_path):
            return model_path
        
        # Check in project models directory
        base_dir = Path(__file__).parent.parent.parent
        models_dir = base_dir / "models" / "vosk"
        
        # Try specific model size
        model_name = self.MODELS.get(model_size, self.MODELS["small"])
        specific_path = models_dir / model_name
        if specific_path.exists():
            return str(specific_path)
        
        # Try any model in the directory
        if models_dir.exists():
            for item in models_dir.iterdir():
                if item.is_dir() and item.name.startswith("vosk-model"):
                    return str(item)
        
        # Create models directory for user to add model
        models_dir.mkdir(parents=True, exist_ok=True)
        
        return str(models_dir / model_name)
    
    def _get_default_model_dir(self) -> str:
        """Get the default model directory."""
        base_dir = Path(__file__).parent.parent.parent
        return str(base_dir / "models" / "vosk")
    
    def is_ready(self) -> bool:
        """Check if Vosk is ready."""
        return self.model is not None and self.recognizer is not None
    
    def register_callback(self, callback: Callable[[str], None]):
        """Register a callback for transcription results."""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
            print(f"[VOSK] Callback registered: {callback}")
    
    def set_device(self, device_index: int):
        """Set the microphone device index."""
        self.device_index = device_index
        print(f"[VOSK] Using microphone index: {device_index}")
    
    def start_listening(self, device_index: int = None):
        """Start listening for speech."""
        if not self.is_ready():
            print("[VOSK] [ERROR] Model not loaded, cannot start listening")
            return False
        
        if not HAS_SOUNDDEVICE:
            print("[VOSK] [ERROR] sounddevice not available")
            return False
        
        if self.is_listening:
            return True
        
        # Use provided device or default
        if device_index is not None:
            self.device_index = device_index
        
        # Default to device 1 (Maonocaster) if not set
        if self.device_index is None:
            self.device_index = 1
        
        self.stop_event.clear()
        self.is_listening = True
        
        print(f"[VOSK] Starting listener on device {self.device_index}...")
        
        def audio_callback(indata, frames, time_info, status):
            """Callback for audio stream."""
            if status:
                print(f"[VOSK] Audio status: {status}")
            if self.is_listening:
                self.audio_queue.put(bytes(indata))
        
        def listen_loop():
            try:
                # Open audio stream
                with sd.RawInputStream(
                    samplerate=self.sample_rate,
                    blocksize=4000,  # ~250ms chunks
                    device=self.device_index,
                    dtype='int16',
                    channels=1,
                    callback=audio_callback
                ):
                    print("[VOSK] [OK] LISTENING - Say 'Monica initialize'!")
                    
                    while not self.stop_event.is_set():
                        try:
                            data = self.audio_queue.get(timeout=0.5)
                            
                            if self.recognizer.AcceptWaveform(data):
                                result = json.loads(self.recognizer.Result())
                                text = result.get("text", "").strip()
                                if text:
                                    print(f"[VOSK] Recognized: {text}")
                                    self._notify_callbacks(text)
                            else:
                                # Partial result
                                partial = json.loads(self.recognizer.PartialResult())
                                partial_text = partial.get("partial", "")
                                if partial_text:
                                    print(f"[VOSK] Partial: {partial_text}", end='\r')
                                    
                        except queue.Empty:
                            continue
                        except Exception as e:
                            if not self.stop_event.is_set():
                                print(f"[VOSK] Processing error: {e}")
                            
            except Exception as e:
                print(f"[VOSK] [ERROR] Stream error: {e}")
            finally:
                self.is_listening = False
                print("[VOSK] Stopped listening")
        
        self.listen_thread = threading.Thread(target=listen_loop, daemon=True)
        self.listen_thread.start()
        return True
    
    def stop_listening(self):
        """Stop listening for speech."""
        self.stop_event.set()
        self.is_listening = False
        # Clear the queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except:
                pass
    
    def _notify_callbacks(self, text: str):
        """Notify all registered callbacks."""
        for callback in self.callbacks:
            try:
                callback(text)
            except Exception as e:
                print(f"[VOSK] Callback error: {e}")
    
    def recognize_audio(self, audio_data: np.ndarray) -> str:
        """Recognize speech from audio data."""
        if not self.is_ready():
            return ""
        
        try:
            # Convert to bytes if needed
            if isinstance(audio_data, np.ndarray):
                if audio_data.dtype == np.float32:
                    audio_data = (audio_data * 32767).astype(np.int16)
                audio_bytes = audio_data.tobytes()
            else:
                audio_bytes = audio_data
            
            # Create new recognizer for this audio
            rec = KaldiRecognizer(self.model, self.sample_rate)
            rec.AcceptWaveform(audio_bytes)
            result = json.loads(rec.FinalResult())
            return result.get("text", "")
            
        except Exception as e:
            print(f"[VOSK] Recognition error: {e}")
            return ""


# Singleton instance
_vosk_instance = None

def get_vosk_stt(model_path: str = None, model_size: str = "small") -> VoskSTT:
    """Get or create Vosk STT instance."""
    global _vosk_instance
    if _vosk_instance is None:
        _vosk_instance = VoskSTT(model_path=model_path, model_size=model_size)
    return _vosk_instance
