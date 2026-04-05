"""
Text-to-Speech Manager for Monica AI.
Supports multiple TTS engines: Coqui TTS, Piper, system TTS.
"""
# CRITICAL: Patch torch.load BEFORE any TTS imports (PyTorch 2.6 compatibility)
try:
    from ..audio import torch_patch  # noqa: F401
except ImportError:
    pass  # Patch may already be applied

import numpy as np
import queue
import threading
import time
import subprocess
import sys
import os
import wave
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass

# Safe defaults for optional imports used throughout this module.
normalize_text_for_tts: Callable[[str], str] = lambda t: t
get_text_normalizer: Optional[Callable[..., Any]] = None
ProsodyEnhancer: Optional[Any] = None
ProsodyStyle: Optional[Any] = None
NeMoNormalizer: Optional[Any] = None
is_nemo_available: Callable[[], bool] = lambda: False
sd: Optional[Any] = None
pygame: Optional[Any] = None
CoquiTTS: Optional[Any] = None

# Import text normalizer for proper pronunciation (lazy-loaded internally)
try:
    from .text_normalizer import normalize_text_for_tts, get_text_normalizer
    HAS_TEXT_NORMALIZER = True
    # Note: num2words and inflect are lazy-loaded on first TTS use
except ImportError:
    HAS_TEXT_NORMALIZER = False
    print("[TTS] Text normalizer not available - using fallback")

# Import prosody enhancer for better rhythm and intonation
try:
    from .prosody_enhancer import ProsodyEnhancer, ProsodyStyle
    HAS_PROSODY_ENHANCER = True
except ImportError:
    HAS_PROSODY_ENHANCER = False
    print("[TTS] Prosody enhancer not available")

# Import NeMo Text Processing for grammar-based normalization
try:
    from .nemo_normalizer import NeMoNormalizer, is_nemo_available
    HAS_NEMO = is_nemo_available()
    if HAS_NEMO:
        print("[TTS] NeMo Text Processing available (grammar-based normalization)")
except ImportError:
    HAS_NEMO = False

# Try to import audio playback
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

# Optional pygame fallback for audio playback (helps on some Windows setups)
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

# Coqui TTS is slow to import and not used (Piper is primary)
# Defer import to avoid slowing down startup
COQUI_AVAILABLE = False
# Note: To enable Coqui, uncomment below:
# try:
#     from TTS.api import TTS as CoquiTTS
#     COQUI_AVAILABLE = True
#     print("[TTS] Coqui TTS available")
# except ImportError:
#     COQUI_AVAILABLE = False
#     print("[TTS] Coqui TTS not available")

# Monica TTS with XTTS and neural lattice effects (trained voice)
MONICA_TTS_AVAILABLE = False
_monica_tts_instance = None

def get_monica_tts():
    """Get or create MonicaTTS instance (lazy singleton)."""
    global _monica_tts_instance, MONICA_TTS_AVAILABLE
    if _monica_tts_instance is None:
        try:
            from ..audio.monica_tts import MonicaTTS
            _monica_tts_instance = MonicaTTS(
                use_gpu=True,
                enable_effects=True,
                effect_preset='quantum'
            )
            MONICA_TTS_AVAILABLE = True
            print("[TTS] Monica XTTS with neural lattice effects available")
        except Exception as e:
            print(f"[TTS] Monica TTS not available: {e}")
            MONICA_TTS_AVAILABLE = False
    return _monica_tts_instance


@dataclass
class TTSResult:
    """Container for TTS synthesis result."""
    audio_data: np.ndarray
    sample_rate: int
    text: str
    duration: float


class TTSManager:
    """
    Manages text-to-speech synthesis for Monica AI.
    
    Features:
    - Multiple TTS engine support (Piper, system TTS)
    - Voice model management
    - Speed and pitch control
    - Non-blocking synthesis and playback
    - Audio callback support
    """
    
    # Available Piper voice models
    PIPER_VOICES = {
        'en_US-lessac-medium': {
            'language': 'en',
            'quality': 'medium',
            'gender': 'female',
            'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx'
        },
        'en_US-amy-medium': {
            'language': 'en',
            'quality': 'medium',
            'gender': 'female',
            'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx'
        },
        'en_US-ryan-medium': {
            'language': 'en',
            'quality': 'medium',
            'gender': 'male',
            'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx'
        },
        'en_GB-alba-medium': {
            'language': 'en',
            'quality': 'medium',
            'gender': 'female',
            'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/en_GB-alba-medium.onnx'
        }
    }
    
    def __init__(self, config):
        """
        Initialize the TTS manager.
        
        Args:
            config: Application configuration object
        """
        self.config = config
        self.voices_dir = config.VOICES_DIR
        
        # TTS state
        self.current_voice = config.DEFAULT_VOICE_MODEL
        self.speed = config.TTS_SPEED
        self.pitch = config.TTS_PITCH
        
        # Engine
        self.engine = None
        self.engine_type = config.TTS_ENGINE
        self.is_initialized = False
        self.sample_rate = 22050  # Default, will be updated by Piper
        
        # Monica XTTS with neural lattice effects (trained voice)
        self.use_monica_tts = getattr(config, 'USE_MONICA_TTS', True)  # Default to trained voice
        self.monica_tts = None
        
        # Playback
        self.is_speaking = False
        self.stop_event = threading.Event()
        self.audio_queue = queue.Queue()
        self.playback_thread = None
        
        # Callbacks
        self.start_callbacks: List[Callable[[str], None]] = []
        self.end_callbacks: List[Callable[[str], None]] = []
        self.audio_callbacks: List[Callable[[np.ndarray], None]] = []
        # Optional input-activity callback for anti-barge-in
        self.is_user_speaking_callback: Optional[Callable[[], bool]] = None
        self.enable_anti_barge_in: bool = True
        self.stop_on_user_speech: bool = False  # FIXED: Prevent mid-sentence cutoffs
        self.required_silence_ms: int = 100  # REDUCED: Faster response (was 200ms)

        # CRITICAL: Reference to speech recognizer for echo cancellation
        # Set this externally after AudioManager is created
        self.speech_recognizer = None
        self.stt_pause_cooldown_ms: int = 400  # Wait after TTS before resuming STT

        self.debug_dump_wav: bool = bool(os.getenv('MONICA_TTS_DUMP_WAV', '').strip())
        self.debug_dump_dir: Path = Path(os.getenv('MONICA_TTS_DUMP_DIR', str(Path.cwd() / 'tts_debug')))

        if self.debug_dump_wav:
            try:
                print(f"[TTS] Debug WAV dump enabled (MONICA_TTS_DUMP_WAV=1). Output dir: {self.debug_dump_dir}")
            except Exception:
                pass
        
        # Initialize TTS engine (try Piper first - it's faster and more reliable)
        # Coqui is slower and can cause delays
        self._init_piper()
        
        if not self.is_initialized and COQUI_AVAILABLE:
            self._init_coqui()
        
        if not self.is_initialized:
            self._init_system_tts()
        
        print(f"TTS Manager ready: engine={self.engine_type}, initialized={self.is_initialized}")
        
        # Don't pre-generate startup sounds - wait for user to initialize
        # self._pregenerate_startup_sounds()

    def preload_xtts_model(self):
        """
        Pre-load the XTTS model in background to eliminate lag on first conversation.
        Call this after startup sequence completes.
        """
        def _preload():
            try:
                print("[TTS] Pre-loading XTTS model in background...")
                monica_tts = get_monica_tts()
                if monica_tts is not None:
                    # Trigger lazy initialization by calling _lazy_init
                    if hasattr(monica_tts, '_lazy_init'):
                        monica_tts._lazy_init()
                    print("[TTS] [OK] XTTS model pre-loaded and ready for instant response!")
                else:
                    print("[TTS] XTTS model not available")
            except Exception as e:
                print(f"[TTS] XTTS pre-load error: {e}")
        
        # Run in background thread so it doesn't block
        import threading
        threading.Thread(target=_preload, daemon=True).start()

    def _pause_stt(self):
        """Pause STT to prevent TTS echo from being transcribed."""
        try:
            rec = self.speech_recognizer
            if rec is None:
                return
            if hasattr(rec, 'flush'):
                rec.flush()
            if hasattr(rec, 'pause'):
                rec.pause()
            print("[TTS] Paused STT for TTS playback")
        except Exception as e:
            print(f"[TTS] Failed to pause STT: {e}")

    def _resume_stt(self, delay_ms: Optional[int] = None):
        """Resume STT after TTS playback with optional cooldown."""
        if delay_ms is None:
            delay_ms = self.stt_pause_cooldown_ms
        try:
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            rec = self.speech_recognizer
            if rec is None:
                return
            if hasattr(rec, 'flush'):
                rec.flush()
            if hasattr(rec, 'resume'):
                rec.resume()
            print("[TTS] Resumed STT after TTS playback")
        except Exception as e:
            print(f"[TTS] Failed to resume STT: {e}")

    def _dump_debug_wav(self, audio_data: np.ndarray, sample_rate: int, tag: str = "tts") -> Optional[Path]:
        try:
            if not self.debug_dump_wav:
                return None
            if audio_data is None or len(audio_data) == 0:
                return None

            self.debug_dump_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            safe_tag = ''.join([c for c in (tag or 'tts') if c.isalnum() or c in ('-', '_')])[:24]
            out_path = self.debug_dump_dir / f"{safe_tag}_{ts}_{sample_rate}hz.wav"

            x = audio_data
            if isinstance(x, np.ndarray) and x.dtype != np.float32:
                x = x.astype(np.float32)
            if x.ndim > 1:
                x = np.mean(x, axis=1).astype(np.float32)
            x = np.clip(x, -1.0, 1.0)
            pcm = (x * 32767.0).astype(np.int16)

            with wave.open(str(out_path), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(int(sample_rate))
                wf.writeframes(pcm.tobytes())

            print(f"[TTS] Debug WAV written: {out_path}")
            return out_path
        except Exception as e:
            print(f"[TTS] Debug WAV dump failed: {e}")
            return None
    
    def _init_coqui(self):
        """Initialize Coqui TTS engine."""
        try:
            print("[TTS] Initializing Coqui TTS...")
            
            # Use a good quality model - jenny is natural sounding
            # Other options: tts_models/en/ljspeech/tacotron2-DDC, tts_models/en/vctk/vits
            model_name = "tts_models/en/ljspeech/tacotron2-DDC"
            
            if CoquiTTS is None:
                raise RuntimeError("Coqui TTS class unavailable")
            self.coqui_tts = CoquiTTS(model_name=model_name, progress_bar=False)
            
            # Get sample rate from model
            if hasattr(self.coqui_tts, 'synthesizer') and self.coqui_tts.synthesizer:
                self.sample_rate = self.coqui_tts.synthesizer.output_sample_rate
            else:
                self.sample_rate = 22050
            
            self.engine_type = 'coqui'
            self.is_initialized = True
            print(f"[TTS] Coqui TTS initialized (sample_rate={self.sample_rate})")
            
        except Exception as e:
            print(f"[TTS] Coqui TTS initialization failed: {e}")
            self.coqui_tts = None
    
    def _init_piper(self):
        """Initialize Piper TTS engine."""
        try:
            # Check if piper is installed
            try:
                from piper import PiperVoice
                self._piper_available = True
            except ImportError:
                print("Piper TTS not installed. Using system TTS fallback.")
                self._init_system_tts()
                return
            
            # Load voice model
            model_path = self._get_voice_model_path(self.current_voice)
            print(f"Looking for voice model at: {model_path}")
            
            if model_path and model_path.exists():
                print(f"Loading Piper voice model: {model_path}")
                self.engine = PiperVoice.load(str(model_path))
                self.engine_type = 'piper'
                self.sample_rate = self.engine.config.sample_rate
                
                # Set speaker ID for multi-speaker models (92 = young feminine voice)
                self.speaker_id = 92 if self.engine.config.num_speakers > 1 else None
                
                self.is_initialized = True
                print(f"Piper TTS initialized with voice: {self.current_voice} (sample_rate={self.sample_rate}, speakers={self.engine.config.num_speakers})")
            else:
                print(f"Voice model not found: {self.current_voice}")
                self._init_system_tts()
            
        except Exception as e:
            print(f"Error initializing Piper TTS: {e}")
            import traceback
            traceback.print_exc()
            self._init_system_tts()
    
    def _init_system_tts(self):
        """Initialize system TTS as fallback."""
        try:
            import pyttsx3  # type: ignore[import-not-found]
            self.engine = pyttsx3.init()
            self.engine_type = 'system'
            
            # Configure voice - try to find a female voice
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if 'zira' in voice.name.lower() or 'female' in voice.name.lower():
                    self.engine.setProperty('voice', voice.id)
                    break
            
            # Set rate (slightly slower for clarity)
            self.engine.setProperty('rate', 175)
            
            self.is_initialized = True
            print("System TTS initialized (pyttsx3)")
        except ImportError:
            print("pyttsx3 not installed. TTS will be limited.")
            self.is_initialized = False
        except Exception as e:
            print(f"Error initializing system TTS: {e}")
            self.is_initialized = False
    
    def _get_voice_model_path(self, voice_name: str) -> Optional[Path]:
        """Get the path to a voice model."""
        # Check in voices directory
        model_path = self.voices_dir / f"{voice_name}.onnx"
        if model_path.exists():
            return model_path
        
        # Check for directory with model
        model_dir = self.voices_dir / voice_name
        if model_dir.exists():
            onnx_file = model_dir / f"{voice_name}.onnx"
            if onnx_file.exists():
                return onnx_file
        
        return None
    
    def _download_voice_model(self, voice_name: str) -> bool:
        """Download a Piper voice model."""
        if voice_name not in self.PIPER_VOICES:
            print(f"Unknown voice model: {voice_name}")
            return False
        
        voice_info = self.PIPER_VOICES[voice_name]
        url = voice_info['url']
        
        try:
            import requests
            
            # Create voice directory
            voice_dir = self.voices_dir / voice_name
            voice_dir.mkdir(parents=True, exist_ok=True)
            
            # Download ONNX model
            print(f"Downloading {voice_name}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            model_path = voice_dir / f"{voice_name}.onnx"
            with open(model_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Download JSON config
            json_url = url.replace('.onnx', '.onnx.json')
            response = requests.get(json_url)
            if response.status_code == 200:
                json_path = voice_dir / f"{voice_name}.onnx.json"
                with open(json_path, 'w') as f:
                    f.write(response.text)
            
            print(f"Voice model downloaded: {voice_name}")
            return True
            
        except Exception as e:
            print(f"Error downloading voice model: {e}")
            return False
    
    def _clean_text_for_speech(self, text: str) -> str:
        """
        Clean text for natural speech output.
        - Removes symbols and markdown
        - Converts emotion expressions to natural sounds
        - Handles abbreviations
        """
        import re

        # Remove bracketed/parenthetical asides entirely (these read poorly in local TTS)
        try:
            text = re.sub(r'\([^)]*\)', '', text)
            text = re.sub(r'\[[^\]]*\]', '', text)
            text = re.sub(r'\{[^}]*\}', '', text)
        except Exception:
            pass
        
        # Convert emotion expressions to natural vocalizations
        emotion_replacements = {
            # Laughter
            r'\*laughs?\*': 'ha ha ha',
            r'\*laughing\*': 'ha ha ha',
            r'\*chuckles?\*': 'heh heh',
            r'\*chuckling\*': 'heh heh',
            r'\*giggles?\*': 'hee hee',
            r'\*giggling\*': 'hee hee',
            r'\blol\b': 'ha ha',
            r'\blmao\b': 'ha ha ha',
            r'\brofl\b': 'ha ha ha',
            r'\bhaha+\b': 'ha ha ha',
            r'\bhehe+\b': 'heh heh',
            r'\bhihi+\b': 'hee hee',
            
            # Other emotions
            r'\*sighs?\*': 'sigh',
            r'\*sighing\*': 'sigh',
            r'\*gasps?\*': 'gasp',
            r'\*smiles?\*': '',
            r'\*smiling\*': '',
            r'\*grins?\*': '',
            r'\*grinning\*': '',
            r'\*winks?\*': '',
            r'\*nods?\*': '',
            r'\*nodding\*': '',
            r'\*shrugs?\*': '',
            r'\*waves?\*': '',
            r'\*waving\*': '',
            r'\*thinks?\*': 'hmm',
            r'\*thinking\*': 'hmm',
            r'\*pauses?\*': '',
            r'\*clears throat\*': 'ahem',
        }
        
        for pattern, replacement in emotion_replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Remove remaining asterisk expressions
        text = re.sub(r'\*[^*]+\*', '', text)
        
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Italic
        text = re.sub(r'__([^_]+)__', r'\1', text)  # Bold
        text = re.sub(r'_([^_]+)_', r'\1', text)  # Italic
        text = re.sub(r'~~([^~]+)~~', r'\1', text)  # Strikethrough
        text = re.sub(r'`([^`]+)`', r'\1', text)  # Code
        
        # Remove bullet points and list markers
        text = re.sub(r'^[\s]*[-•*]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\s]*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # Remove hashtags but keep the word
        text = re.sub(r'#(\w+)', r'\1', text)
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)

        # Normalize spaced digit years like "2 0 2 5" -> "2025" or "202 5" -> "2025"
        # This is a common ASR/LLM artifact where years get split
        try:
            # First: Handle partially spaced years like "202 5", "20 25", "2 025"
            text = re.sub(r'\b(20)(\d)\s+(\d)\b', r'\1\2\3', text)  # "202 5" -> "2025"
            text = re.sub(r'\b(20)\s+(\d{2})\b', r'\1\2', text)     # "20 25" -> "2025"
            text = re.sub(r'\b(2)\s+(0\d{2})\b', r'\1\2', text)     # "2 025" -> "2025"
            text = re.sub(r'\b(19)(\d)\s+(\d)\b', r'\1\2\3', text)  # "199 0" -> "1990"
            text = re.sub(r'\b(19)\s+(\d{2})\b', r'\1\2', text)     # "19 90" -> "1990"
            # Then: Handle fully spaced digits "2 0 2 5" -> "2025"
            text = re.sub(r'\b(\d)(?:\s+(\d)){1,5}\b', lambda m: m.group(0).replace(' ', ''), text)
        except Exception:
            pass
        
        # Remove emojis/symbols (keep text clean for TTS)
        text = re.sub(r'[^\w\s.,!?\'"-:;]+', '', text)
        
        # Remove leading/trailing whitespace and punctuation that causes pauses
        text = text.strip()
        text = re.sub(r'^[,;:.!?\s]+', '', text)
        
        # Apply text normalization for better pronunciation
        use_nemo = False
        try:
            use_nemo = bool(os.getenv('MONICA_TTS_USE_NEMO', '').strip())
        except Exception:
            use_nemo = False

        if HAS_NEMO and use_nemo:
            try:
                if NeMoNormalizer is None:
                    raise RuntimeError("NeMo normalizer unavailable")
                if not hasattr(self, '_nemo_normalizer') or self._nemo_normalizer is None:
                    self._nemo_normalizer = NeMoNormalizer(language='en')
                text = self._nemo_normalizer.normalize(text)
            except Exception:
                pass

        if HAS_TEXT_NORMALIZER:
            text = normalize_text_for_tts(text)
        else:
            # Fallback to old methods if no normalizer available
            text = self._convert_iso_datetime_to_spoken(text)
            text = self._convert_times_to_spoken(text)
            text = self._convert_years_to_spoken(text)
            text = self._convert_dates_to_spoken(text)
            text = self._convert_numbers_to_spoken(text)
        
        # Apply prosody enhancement for better rhythm and natural pauses
        # This fixes issues like unnatural pauses at sentence starts
        if HAS_PROSODY_ENHANCER:
            try:
                if ProsodyEnhancer is None or ProsodyStyle is None:
                    raise RuntimeError("Prosody enhancer unavailable")
                if not hasattr(self, '_prosody_enhancer'):
                    self._prosody_enhancer = ProsodyEnhancer(style=ProsodyStyle.CONVERSATIONAL)
                text = self._prosody_enhancer.enhance(text)
            except Exception as e:
                print(f"[TTS] Prosody enhancement error: {e}")
        
        # Clean up extra whitespace but preserve single spaces between words
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Collapse repeated trailing punctuation to avoid "dot dot" pronunciation
        text = re.sub(r'([.!?]){2,}', r'\1', text)
        text = re.sub(r'\s*([.!?])\s*$', r'\1', text)
        
        # Normalize apostrophes and quotes
        text = text.replace("'", "'")
        text = text.replace(""", '"').replace(""", '"')
        text = text.replace("'", "'").replace("'", "'")
        
        # FIX: Prevent Piper from pausing mid-word on contractions
        # Replace contractions with full words to prevent "Wha..." pauses
        contractions = {
            "What's": "What is",
            "what's": "what is",
            "That's": "That is",
            "that's": "that is",
            "It's": "It is",
            "it's": "it is",
            "I'm": "I am",
            "I've": "I have",
            "I'll": "I will",
            "I'd": "I would",
            "You're": "You are",
            "you're": "you are",
            "You've": "You have",
            "you've": "you have",
            "You'll": "You will",
            "you'll": "you will",
            "We're": "We are",
            "we're": "we are",
            "We've": "We have",
            "we've": "we have",
            "They're": "They are",
            "they're": "they are",
            "They've": "They have",
            "they've": "they have",
            "There's": "There is",
            "there's": "there is",
            "Here's": "Here is",
            "here's": "here is",
            "Who's": "Who is",
            "who's": "who is",
            "Let's": "Let us",
            "let's": "let us",
            "Can't": "Cannot",
            "can't": "cannot",
            "Won't": "Will not",
            "won't": "will not",
            "Don't": "Do not",
            "don't": "do not",
            "Doesn't": "Does not",
            "doesn't": "does not",
            "Didn't": "Did not",
            "didn't": "did not",
            "Isn't": "Is not",
            "isn't": "is not",
            "Aren't": "Are not",
            "aren't": "are not",
            "Wasn't": "Was not",
            "wasn't": "was not",
            "Weren't": "Were not",
            "weren't": "were not",
            "Haven't": "Have not",
            "haven't": "have not",
            "Hasn't": "Has not",
            "hasn't": "has not",
            "Hadn't": "Had not",
            "hadn't": "had not",
            "Couldn't": "Could not",
            "couldn't": "could not",
            "Wouldn't": "Would not",
            "wouldn't": "would not",
            "Shouldn't": "Should not",
            "shouldn't": "should not",
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        # FIX: Convert ordinals like "20th" to "twentieth" BEFORE other processing
        import num2words
        def ordinal_to_words(match):
            num = int(match.group(1))
            try:
                return num2words.num2words(num, to='ordinal')
            except:
                return match.group(0)
        
        # Convert ordinals (1st, 2nd, 3rd, 20th, etc.)
        text = re.sub(r'\b(\d+)(?:st|nd|rd|th)\b', ordinal_to_words, text, flags=re.IGNORECASE)
        
        # FIX: Convert standalone 2-digit numbers to words (like "20" -> "twenty")
        def num_to_words(match):
            num = int(match.group(0))
            if num <= 99:
                try:
                    return num2words.num2words(num)
                except:
                    pass
            return match.group(0)
        
        text = re.sub(r'\b(\d{1,2})\b', num_to_words, text)
        
        # FIX: Piper pauses on periods followed by "I" - remove the period entirely
        text = text.replace('. I ', ' I ')
        text = text.replace('.I ', ' I ')
        text = text.replace(', I ', ' I ')  # Also remove comma before I
        
        # Keep sentence boundaries but reduce harsh punctuation
        text = text.replace('!', '.').replace('?', '.')
        
        # Clean up extra spaces and punctuation
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s*,\s*', ', ', text)
        text = re.sub(r',\s*,', ',', text)
        
        # FINAL SAFETY: Convert any remaining 4-digit numbers (years) that weren't caught
        # This is critical for Piper which reads digits individually
        import num2words
        def convert_remaining_year(match):
            year = int(match.group(0))
            if 1900 <= year <= 2099:
                try:
                    result = num2words.num2words(year, to='year')
                    # FIX: Replace spaces with hyphens to prevent Piper from pausing
                    result = result.replace(' ', '-')
                    print(f"[TTS] Final year conversion: {year} -> {result}")
                    return result
                except:
                    pass
            return match.group(0)
        
        text = re.sub(r'\b(19\d{2}|20\d{2})\b', convert_remaining_year, text)
        
        # Final cleanup
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _split_text_for_speech(self, text: str) -> List[str]:
        import re
        t = (text or '').strip()
        if not t:
            return []
        t = re.sub(r'\s+', ' ', t).strip()
        if len(t) <= 220:
            return [t]
        parts = re.split(r'(?<=[.!?])\s+|\s*;\s*|\s*:\s*', t)
        out: List[str] = []
        buf = ''
        for p in parts:
            p = (p or '').strip()
            if not p:
                continue
            if not buf:
                buf = p
            elif len(buf) + 1 + len(p) <= 220:
                buf = f"{buf} {p}"
            else:
                out.append(buf)
                buf = p
        if buf:
            out.append(buf)
        return out
    
    def _convert_years_to_spoken(self, text: str) -> str:
        """Convert years like 2025 to 'twenty twenty-five', 1879 to 'eighteen seventy-nine'."""
        import re
        
        # Number words
        ones = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
                'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen',
                'seventeen', 'eighteen', 'nineteen']
        tens = ['', 'ten', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
        
        def two_digit_to_words(num):
            """Convert a two-digit number to words."""
            if num == 0:
                return ""
            elif num < 20:
                return ones[num]
            else:
                ten = num // 10
                unit = num % 10
                if unit == 0:
                    return tens[ten]
                else:
                    return f"{tens[ten]}-{ones[unit]}"
        
        def year_to_words(year_str):
            year = int(year_str)
            
            # Handle 2000-2009 specially (two thousand, two thousand one, etc.)
            if 2000 <= year <= 2009:
                if year == 2000:
                    return "two thousand"
                else:
                    return f"two thousand {ones[year - 2000]}"
            
            # Handle 2010-2099 (twenty ten, twenty twenty-five, etc.)
            # Use hyphen to prevent Piper from pausing: "twenty-twenty-five"
            if 2010 <= year <= 2099:
                first_half = 20  # "twenty"
                second_half = year - 2000  # e.g., 25 for 2025
                return f"twenty-{two_digit_to_words(second_half)}"
            
            # Handle 1000-1999 (e.g., 1879 -> eighteen seventy-nine, 1989 -> nineteen eighty-nine)
            if 1000 <= year <= 1999:
                first_half = year // 100  # e.g., 18 for 1879, 19 for 1989
                second_half = year % 100   # e.g., 79 for 1879, 89 for 1989
                
                # Convert first half (10-19)
                if first_half < 10:
                    first_word = ones[first_half]
                else:
                    first_word = tens[first_half // 10]
                    if first_half % 10 != 0:
                        first_word = f"{first_word}-{ones[first_half % 10]}"
                
                # Convert second half
                second_word = two_digit_to_words(second_half)
                
                # Combine with proper spacing
                if second_word:
                    return f"{first_word} {second_word}"
                else:
                    return first_word
            
            # For other numbers, just return as-is
            return year_str
        
        # Find 4-digit years (1000-2099) and convert them
        def replace_year(match):
            original = match.group(0)
            converted = year_to_words(original)
            print(f"[TTS] Year conversion: {original} -> {converted}")
            return converted
        
        text = re.sub(r'\b(1[0-9]{3}|20[0-9]{2})\b', replace_year, text)
        
        return text
    
    def _convert_numbers_to_spoken(self, text: str) -> str:
        """Convert standalone numbers to spoken form (42 -> forty-two)."""
        import re
        
        ones = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
                'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen',
                'seventeen', 'eighteen', 'nineteen']
        tens = ['', 'ten', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
        
        def number_to_words(num):
            """Convert a number (0-999) to words."""
            if num < 20:
                return ones[num]
            elif num < 100:
                ten = num // 10
                unit = num % 10
                if unit == 0:
                    return tens[ten]
                else:
                    return f"{tens[ten]}-{ones[unit]}"
            elif num < 1000:
                hundred = num // 100
                remainder = num % 100
                if remainder == 0:
                    return f"{ones[hundred]} hundred"
                else:
                    return f"{ones[hundred]} hundred {number_to_words(remainder)}"
            return str(num)
        
        def replace_number(match):
            num = int(match.group(0))
            # Only convert numbers 0-999 that aren't years
            if 0 <= num <= 999:
                return number_to_words(num)
            return match.group(0)
        
        # Convert standalone 1-3 digit numbers (not part of larger numbers or years)
        # Avoid converting numbers that are part of times (e.g., 2:30)
        text = re.sub(r'(?<![:\d])\b([0-9]{1,3})\b(?![:\d])', replace_number, text)
        
        return text
    
    def _convert_dates_to_spoken(self, text: str) -> str:
        """Convert date numbers to ordinals (06 -> sixth, 21 -> twenty-first)."""
        import re
        
        ordinals = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth',
            6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth',
            11: 'eleventh', 12: 'twelfth', 13: 'thirteenth', 14: 'fourteenth',
            15: 'fifteenth', 16: 'sixteenth', 17: 'seventeenth', 18: 'eighteenth',
            19: 'nineteenth', 20: 'twentieth', 21: 'twenty-first', 22: 'twenty-second',
            23: 'twenty-third', 24: 'twenty-fourth', 25: 'twenty-fifth',
            26: 'twenty-sixth', 27: 'twenty-seventh', 28: 'twenty-eighth',
            29: 'twenty-ninth', 30: 'thirtieth', 31: 'thirty-first'
        }
        
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        
        # Convert "December 06" or "December 6" or "December 7th" to "December sixth/seventh"
        for month in months:
            # Pattern for "Month DD" or "Month D"
            pattern = rf'({month})\s+0?(\d{{1,2}})(?:st|nd|rd|th)?'
            def replace_date(match, m=month, ords=ordinals):
                month_name = match.group(1)
                day = int(match.group(2))
                if day in ords:
                    return f"{month_name} {ords[day]}"
                return match.group(0)
            text = re.sub(pattern, replace_date, text, flags=re.IGNORECASE)
        
        return text

    def _convert_iso_datetime_to_spoken(self, text: str) -> str:
        """Convert ISO-like datetimes (YYYY-MM-DD[ T]HH:MM[:SS]) to spoken form."""
        import re
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                  'July', 'August', 'September', 'October', 'November', 'December']
        ordinals = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth',
            6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth',
            11: 'eleventh', 12: 'twelfth', 13: 'thirteenth', 14: 'fourteenth',
            15: 'fifteenth', 16: 'sixteenth', 17: 'seventeenth', 18: 'eighteenth',
            19: 'nineteenth', 20: 'twentieth', 21: 'twenty-first', 22: 'twenty-second',
            23: 'twenty-third', 24: 'twenty-fourth', 25: 'twenty-fifth',
            26: 'twenty-sixth', 27: 'twenty-seventh', 28: 'twenty-eighth',
            29: 'twenty-ninth', 30: 'thirtieth', 31: 'thirty-first'
        }
        
        def month_name(m: int) -> str:
            if 1 <= m <= 12:
                return months[m-1]
            return ''
        
        def day_ord(d: int) -> str:
            return ordinals.get(d, str(d))
        
        def time_words(h: int, mi: int) -> str:
            # Convert 24h to 12h with AM/PM
            ampm = 'AM' if h < 12 else 'PM'
            h12 = h % 12
            h12 = 12 if h12 == 0 else h12
            numbers = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
                       'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty',
                       'twenty-one', 'twenty-two', 'twenty-three', 'twenty-four', 'twenty-five', 'twenty-six', 'twenty-seven', 'twenty-eight', 'twenty-nine',
                       'thirty', 'thirty-one', 'thirty-two', 'thirty-three', 'thirty-four', 'thirty-five', 'thirty-six', 'thirty-seven', 'thirty-eight', 'thirty-nine',
                       'forty', 'forty-one', 'forty-two', 'forty-three', 'forty-four', 'forty-five', 'forty-six', 'forty-seven', 'forty-eight', 'forty-nine',
                       'fifty', 'fifty-one', 'fifty-two', 'fifty-three', 'fifty-four', 'fifty-five', 'fifty-six', 'fifty-seven', 'fifty-eight', 'fifty-nine']
            if mi == 0:
                return f"{numbers[h12]} {ampm}"
            if mi < len(numbers):
                return f"{numbers[h12]} {numbers[mi]} {ampm}"
            return f"{numbers[h12]} {mi:02d} {ampm}"
        
        # Pattern: YYYY-MM-DD[ T]HH:MM[:SS]
        pattern_dt = re.compile(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})[ T](\d{1,2}):(\d{2})(?::(\d{2}))?\b")
        # Pattern: YYYY-MM-DD only
        pattern_d = re.compile(r"\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b")
        
        def repl_dt(m):
            y = int(m.group(1)); mo = int(m.group(2)); d = int(m.group(3))
            h = int(m.group(4)); mi = int(m.group(5))
            date_str = f"{month_name(mo)} {day_ord(d)}, {self._convert_years_to_spoken(str(y))}"
            return f"{date_str} at {time_words(h, mi)}"
        
        text = pattern_dt.sub(repl_dt, text)
        
        def repl_d(m):
            y = int(m.group(1)); mo = int(m.group(2)); d = int(m.group(3))
            return f"{month_name(mo)} {day_ord(d)}, {self._convert_years_to_spoken(str(y))}"
        
        text = pattern_d.sub(repl_d, text)
        return text

    def _convert_times_to_spoken(self, text: str) -> str:
        """Convert standalone times like 14:05 or 7:30 to spoken form."""
        import re
        def repl_time(m):
            h = int(m.group(1)); mi = int(m.group(2))
            ampm = 'AM' if h < 12 else 'PM'
            h12 = h % 12
            h12 = 12 if h12 == 0 else h12
            numbers = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
                       'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen', 'twenty',
                       'twenty-one', 'twenty-two', 'twenty-three', 'twenty-four', 'twenty-five', 'twenty-six', 'twenty-seven', 'twenty-eight', 'twenty-nine',
                       'thirty', 'thirty-one', 'thirty-two', 'thirty-three', 'thirty-four', 'thirty-five', 'thirty-six', 'thirty-seven', 'thirty-eight', 'thirty-nine',
                       'forty', 'forty-one', 'forty-two', 'forty-three', 'forty-four', 'forty-five', 'forty-six', 'forty-seven', 'forty-eight', 'forty-nine',
                       'fifty', 'fifty-one', 'fifty-two', 'fifty-three', 'fifty-four', 'fifty-five', 'fifty-six', 'fifty-seven', 'fifty-eight', 'fifty-nine']
            if mi == 0:
                return f"{numbers[h12]} {ampm}"
            if mi < len(numbers):
                return f"{numbers[h12]} {numbers[mi]} {ampm}"
            return f"{numbers[h12]} {mi:02d} {ampm}"
        
        return re.sub(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", repl_time, text)
    
    def speak(self, text: str, block: bool = False, use_xtts: Optional[bool] = None) -> bool:
        """
        Synthesize and play speech.
        
        Args:
            text: Text to speak
            block: If True, wait for speech to complete
            use_xtts: If True, use MonicaTTS with neural lattice effects (trained voice)
            
        Returns:
            True if synthesis started successfully
        """
        if not text.strip():
            return False
        
        # Try MonicaTTS with trained voice first (if enabled)
        if use_xtts is None:
            use_xtts = self.use_monica_tts
        
        # RE-ENABLED: MonicaTTS with fixed inference parameters
        # - temperature=0.3 (was 0.7) to prevent garbled/Chinese-sounding output
        # - repetition_penalty=10.0 to prevent loops
        # - speed=1.0 for normal pacing
        # If MonicaTTS fails, will fall back to Piper automatically below
        
        if not self.is_initialized:
            print("TTS not initialized")
            return False
        
        print(f"[TTS] speak() called with: '{text[:100]}...'")
        
        # Clean text for speech - remove symbols and convert emotions to sounds
        text = self._clean_text_for_speech(text)
        
        print(f"[TTS] After cleaning: '{text[:100]}...'")
        
        if not text.strip():
            return False
        
        # Stop any ongoing speech
        if self.is_speaking:
            self.stop()
        
        self.is_speaking = True
        self.stop_event.clear()
        
        # Notify start callbacks
        for callback in self.start_callbacks:
            try:
                callback(text)
            except Exception:
                pass
        
        segments = self._split_text_for_speech(text)

        # Start synthesis in background
        def synthesize_and_play():
            # CRITICAL: Pause STT to prevent TTS echo from being transcribed
            self._pause_stt()
            
            # Set orb speaking indicator (yellow glow)
            try:
                from opencv_window_manager import set_orb_speaking
                set_orb_speaking(True)
            except Exception:
                pass
            
            try:
                first_segment = True
                for seg in segments:
                    if self.stop_event.is_set():
                        break
                    audio_data = self._synthesize(seg, use_xtts_override=use_xtts)
                    if audio_data is not None and not self.stop_event.is_set():
                        try:
                            sr = int(getattr(self, 'sample_rate', 22050))
                            self._dump_debug_wav(audio_data, sr, tag="tts")
                        except Exception:
                            pass
                        for callback in self.audio_callbacks:
                            try:
                                callback(audio_data)
                            except Exception:
                                pass
                        self._play_audio(audio_data, wait_for_silence=first_segment)
                    if self.stop_event.is_set():
                        break
                    first_segment = False
                    time.sleep(0.05)  # REDUCED: Faster segment transitions (was 0.12)
                
            except Exception as e:
                print(f"Error in TTS: {e}")
            finally:
                self.is_speaking = False
                
                # Turn off orb speaking indicator
                try:
                    from opencv_window_manager import set_orb_speaking
                    set_orb_speaking(False)
                except Exception:
                    pass
                
                # Notify end callbacks
                for callback in self.end_callbacks:
                    try:
                        callback(text)
                    except Exception:
                        pass
                
                # CRITICAL: Resume STT after TTS completes (with cooldown)
                self._resume_stt(delay_ms=400)
        
        self.playback_thread = threading.Thread(target=synthesize_and_play, daemon=True)
        self.playback_thread.start()
        
        if block:
            self.wait_until_done()
        
        return True
    
    def _apply_scifi_echo(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply a subtle sci-fi echo effect for elegant spaceship voice.
        Very slight reverb/echo that sounds futuristic but not overwhelming.
        """
        try:
            sample_rate = getattr(self, 'sample_rate', 22050)
            
            # Very subtle echo parameters
            delay_ms = 30  # 30ms delay - very short for subtle effect
            decay = 0.15  # 15% echo strength - very subtle
            
            delay_samples = int(sample_rate * delay_ms / 1000)
            
            # Create output with room for echo
            output = np.zeros(len(audio) + delay_samples * 3, dtype=np.float32)
            output[:len(audio)] = audio
            
            # Add multiple subtle echoes for spaceship reverb effect
            # First echo - very close
            output[delay_samples:delay_samples + len(audio)] += audio * decay
            
            # Second echo - slightly further
            delay2 = int(delay_samples * 1.7)
            output[delay2:delay2 + len(audio)] += audio * (decay * 0.5)
            
            # Third echo - even further (barely audible)
            delay3 = int(delay_samples * 2.5)
            if delay3 + len(audio) <= len(output):
                output[delay3:delay3 + len(audio)] += audio * (decay * 0.25)
            
            # Normalize to prevent clipping
            max_val = np.abs(output).max()
            if max_val > 0.95:
                output = output * (0.95 / max_val)
            
            # Trim silence at end
            output = output[:len(audio) + delay_samples * 2]
            
            return output.astype(np.float32)
            
        except Exception as e:
            print(f"Echo effect error: {e}")
            return audio  # Return original if effect fails
    
    def generate_startup_sound(self) -> Optional[np.ndarray]:
        """
        Generate a sci-fi plasma/electrical startup sound.
        Like a spaceship powering up with electronic buzzing.
        """
        try:
            sample_rate = getattr(self, 'sample_rate', 22050)
            duration = 0.8  # Shorter - 0.8 seconds
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples, dtype=np.float32)
            
            # Rising plasma tone (frequency sweep)
            freq_start = 150
            freq_end = 600
            freq_sweep = freq_start + (freq_end - freq_start) * (t / duration)
            plasma = np.sin(2 * np.pi * freq_sweep * t) * 0.4
            
            # Add one harmonic
            plasma += np.sin(2 * np.pi * freq_sweep * 2 * t) * 0.2
            
            # Apply rising envelope
            envelope = np.clip(t / 0.2, 0, 1) * (1 - (t / duration) ** 3)
            sound = plasma * envelope
            
            # Normalize
            max_val = np.abs(sound).max()
            if max_val > 0:
                sound = sound / max_val * 0.6
            
            return sound.astype(np.float32)
        except Exception as e:
            print(f"Startup sound generation error: {e}")
            return None
    
    def generate_beep_sound(self, freq: int = 800, duration: float = 0.15) -> Optional[np.ndarray]:
        """Generate a simple beep for acknowledgments."""
        try:
            sample_rate = getattr(self, 'sample_rate', 22050)
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples, dtype=np.float32)
            
            # Simple tone with envelope
            tone = np.sin(2 * np.pi * freq * t) * 0.4
            envelope = np.sin(np.pi * t / duration)  # Smooth rise and fall
            sound = tone * envelope
            
            return sound.astype(np.float32)
        except Exception:
            return None
    
    def play_startup_sound(self):
        """Play the sci-fi startup sound."""
        try:
            import sounddevice as sd
            sound = self.generate_startup_sound()
            if sound is not None:
                sample_rate = getattr(self, 'sample_rate', 22050)
                sd.play(sound, sample_rate, blocking=False)
        except Exception as e:
            print(f"Startup sound error: {e}")
    
    def play_acknowledgment_beep(self):
        """Play a quick acknowledgment beep."""
        try:
            import sounddevice as sd
            sound = self.generate_beep_sound(600, 0.1)
            if sound is not None:
                sample_rate = getattr(self, 'sample_rate', 22050)
                sd.play(sound, sample_rate, blocking=False)
        except Exception as e:
            print(f"Beep error: {e}")
    
    def _pregenerate_startup_sounds(self):
        """Pre-generate startup sounds in background for instant 'Monica initialize'."""
        def generate_in_background():
            try:
                print("[TTS] Pre-generating startup sounds...")
                # Generate sci-fi startup sound
                self.generate_scifi_startup_sound()
                # Generate robotic "Monica initializing" voice
                self.generate_robotic_voice("Monica initializing")
                print("[TTS] Startup sounds ready!")
            except Exception as e:
                print(f"[TTS] Pre-generation error: {e}")
        
        # Run in background thread so it doesn't block startup
        import threading
        threading.Thread(target=generate_in_background, daemon=True).start()
    
    def generate_robotic_voice(self, text: str) -> Optional[np.ndarray]:
        """
        Generate a robotic/machine voice for system messages.
        Uses vocoder-like effect with metallic resonance.
        
        Caches "Monica initializing" for faster startup.
        """
        # Check cache for common phrases
        cache_key = f"_cached_robotic_{text.lower().replace(' ', '_')}"
        if hasattr(self, cache_key):
            cached = getattr(self, cache_key)
            if cached is not None:
                return cached
        
        try:
            # First synthesize the text normally
            audio = self._synthesize(text)
            if audio is None:
                return None
            
            sample_rate = getattr(self, 'sample_rate', 22050)
            
            # Apply robotic effects
            # 1. Ring modulation (metallic sound)
            t = np.arange(len(audio)) / sample_rate
            carrier_freq = 50  # Low frequency carrier for robotic effect
            modulator = np.sin(2 * np.pi * carrier_freq * t) * 0.3 + 0.7
            audio = audio * modulator.astype(np.float32)
            
            # 2. Add subtle harmonics
            harmonic = np.sin(2 * np.pi * 150 * t) * 0.1
            audio = audio + harmonic.astype(np.float32)
            
            # 3. Slight bitcrushing effect (reduce resolution)
            bits = 12  # Reduce from 16 to 12 bits
            audio = np.round(audio * (2**bits)) / (2**bits)
            
            # Normalize
            max_val = np.abs(audio).max()
            if max_val > 0:
                audio = audio / max_val * 0.8
            
            result = audio.astype(np.float32)
            
            # Cache for future use
            setattr(self, cache_key, result)
            
            return result
        except Exception as e:
            print(f"Robotic voice error: {e}")
            return None
    
    def generate_scifi_startup_sound(self) -> np.ndarray:
        """
        Generate an impressive sci-fi machine startup sound sequence.
        Optimized for speed: ~1.5 seconds total.
        
        Uses caching to avoid regenerating on each startup.
        """
        # Check cache first
        if hasattr(self, '_cached_startup_sound') and self._cached_startup_sound is not None:
            return self._cached_startup_sound
        
        sample_rate = getattr(self, 'sample_rate', 22050)
        all_audio = []
        
        # 1. Initial power surge (0.15s) - electrical spark
        spark_dur = 0.15
        spark_samples = int(sample_rate * spark_dur)
        spark_t = np.linspace(0, spark_dur, spark_samples, dtype=np.float32)
        spark = np.random.randn(spark_samples).astype(np.float32) * 0.4
        spark_env = np.exp(-spark_t * 12) * (1 + np.sin(2 * np.pi * 60 * spark_t) * 0.5)
        spark = (spark * spark_env).astype(np.float32)
        all_audio.append(spark)
        
        # 2. Main power-up whoosh (0.6 seconds) - turbine spinning up
        duration = 0.6
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples, dtype=np.float32)
        
        # Rising frequency sweep (like turbine spinning up)
        freq = 40 + 600 * (t / duration) ** 2
        powerup = np.sin(2 * np.pi * freq * t) * 0.5
        # Add harmonics for richness
        powerup += np.sin(2 * np.pi * freq * 2 * t) * 0.25
        powerup += np.sin(2 * np.pi * freq * 0.5 * t) * 0.15
        # Electrical hum undertone
        hum = np.sin(2 * np.pi * 60 * t) * 0.1
        powerup = powerup + hum
        # Rising envelope with sustain
        envelope = np.clip(t / 0.3, 0, 1) * (1 - (t / duration) ** 3)
        powerup = (powerup * envelope * 0.7).astype(np.float32)
        all_audio.append(powerup)
        
        # 3. Quick loading beeps (0.3s) - just 3 beeps
        gap = np.zeros(int(sample_rate * 0.03), dtype=np.float32)
        all_audio.append(gap)
        
        # Loading progress beeps - ascending (faster)
        for i in range(3):
            beep_dur = 0.05
            beep_samples = int(sample_rate * beep_dur)
            beep_t = np.linspace(0, beep_dur, beep_samples, dtype=np.float32)
            beep_freq = 500 + i * 150  # Ascending frequency
            beep = np.sin(2 * np.pi * beep_freq * beep_t) * 0.4
            beep_env = np.sin(np.pi * beep_t / beep_dur)
            beep = (beep * beep_env).astype(np.float32)
            all_audio.append(beep)
            all_audio.append(np.zeros(int(sample_rate * 0.03), dtype=np.float32))
        
        # 4. System ready confirmation (0.2s) - triumphant dual tone
        conf_dur = 0.2
        conf_samples = int(sample_rate * conf_dur)
        conf_t = np.linspace(0, conf_dur, conf_samples, dtype=np.float32)
        # Major chord - sounds positive/ready
        conf = np.sin(2 * np.pi * 523 * conf_t) * 0.3  # C5
        conf += np.sin(2 * np.pi * 659 * conf_t) * 0.25  # E5
        conf += np.sin(2 * np.pi * 784 * conf_t) * 0.2  # G5
        conf_env = np.sin(np.pi * conf_t / conf_dur)
        conf = (conf * conf_env).astype(np.float32)
        all_audio.append(conf)
        
        # Combine
        full_audio = np.concatenate(all_audio)
        
        # Normalize
        max_val = np.abs(full_audio).max()
        if max_val > 0:
            full_audio = full_audio / max_val * 0.75
        
        # Cache for future use
        self._cached_startup_sound = full_audio.astype(np.float32)
        return self._cached_startup_sound
    
    def speak_with_startup(self, text: str, on_complete=None, on_progress=None, fast_mode=True):
        """
        Play startup sequence with Monica's intelligent responses and sounds.
        
        Args:
            text: Greeting text to speak after startup
            on_complete: Callback when complete
            on_progress: Callback for progress updates
            fast_mode: If True, use pre-recorded startup audio with Monica's voice
        """
        def startup_thread():
            # Temporarily disable anti-barge-in so Monica is never cut off
            prev_anti = getattr(self, "enable_anti_barge_in", False)
            prev_stop_on_speech = getattr(self, "stop_on_user_speech", False)
            self.enable_anti_barge_in = False
            self.stop_on_user_speech = False

            # CRITICAL: Pause STT BEFORE any TTS audio to prevent echo
            self._pause_stt()

            try:
                print("[TTS] Starting startup sequence in background thread...")
                print(f"[TTS STARTUP] Starting sequence (fast_mode={fast_mode})...")
                
                if fast_mode:
                    # PHASE 1: Play initialization sound from scifi folder
                    if pygame is None:
                        raise RuntimeError("pygame unavailable")
                    if not pygame.mixer.get_init():
                        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                    
                    # Path is monica_ai/resources/sounds/scifi/ (not monica_ai/src/resources/)
                    scifi_sound_path = Path(__file__).parent.parent.parent / "resources" / "sounds" / "scifi" / "monica_initialize_one.mp3"
                    
                    if scifi_sound_path.exists():
                        print(f"[TTS STARTUP] Playing initialization sound: {scifi_sound_path}")
                        
                        # Load sound but DON'T play yet
                        init_sound = pygame.mixer.Sound(str(scifi_sound_path))
                        sound_duration = init_sound.get_length()
                        print(f"[TTS STARTUP] Sound duration: {sound_duration:.2f}s")
                        
                        # Monica's startup phrases (user preference):
                        #  - "Initializing Monica"
                        #  - "Neural lattice forming"
                        #  - "Quantum sync established"
                        #  - "Voice matrix calibrated"
                        startup_phrases = [
                            "Initializing Monica",
                            "Neural lattice forming",
                            "Quantum sync established",
                            "Voice matrix calibrated"
                        ]
                        
                        # Start the initialization sound on channel 0
                        channel_init = pygame.mixer.Channel(0)
                        channel_init.play(init_sound)
                        print(f"[TTS STARTUP] Playing initialization sound ({sound_duration:.1f}s)...")
                        
                        # Load Monica's own sci-fi sounds to play simultaneously
                        scifi_sounds_dir = scifi_sound_path.parent
                        monica_sounds = []
                        for snd_name in ['monica_electricalstart_orb.mp3', 'energy_hum.mp3', 'monica_Orb_forming.mp3']:
                            snd_path = scifi_sounds_dir / snd_name
                            if snd_path.exists():
                                try:
                                    monica_sounds.append(pygame.mixer.Sound(str(snd_path)))
                                except:
                                    pass
                        
                        # Play Monica's sounds on separate channels (layered effect)
                        if monica_sounds:
                            for idx, snd in enumerate(monica_sounds[:3]):
                                try:
                                    ch = pygame.mixer.Channel(idx + 1)
                                    ch.set_volume(0.4)  # Lower volume so they blend
                                    # Stagger the sounds
                                    threading.Timer(idx * 2.0, lambda s=snd, c=ch: c.play(s)).start()
                                except:
                                    pass
                            print(f"[TTS STARTUP] Playing {len(monica_sounds)} additional sci-fi sounds")
                        
                        time.sleep(1.0)  # Let sounds start
                        
                        # Monica speaks DURING the sound with proper timing
                        phrase_interval = max(2.0, (sound_duration - 2.0) / len(startup_phrases))
                        
                        for i, phrase in enumerate(startup_phrases):
                            if self.stop_event.is_set():
                                break
                            
                            print(f"[TTS STARTUP] Monica: {phrase}")
                            # Notify progress (line started)
                            try:
                                if on_progress:
                                    on_progress('tts_line_started', phrase)
                            except Exception:
                                pass
                            
                            # Use Piper for startup (fast and reliable)
                            # MonicaTTS will be used for regular conversation
                            audio_data = self._synthesize_piper(phrase)
                            if audio_data is not None:
                                self._play_audio(audio_data, wait_for_silence=False)
                            # Notify progress (line finished)
                            try:
                                if on_progress:
                                    on_progress('tts_line_finished', phrase)
                            except Exception:
                                pass
                            
                            # Wait before next phrase so lines are spaced across the loading sound
                            if i < len(startup_phrases) - 1:
                                time.sleep(phrase_interval)
                        
                        # Wait for initialization sound to finish COMPLETELY - NO SPEECH UNTIL DONE
                        print("[TTS STARTUP] Waiting for initialization sound to finish...")
                        while channel_init.get_busy():
                            if self.stop_event.is_set():
                                pygame.mixer.stop()
                                break
                            time.sleep(0.1)
                        
                        # Stop any remaining sounds
                        for ch_idx in range(1, 4):
                            try:
                                pygame.mixer.Channel(ch_idx).stop()
                            except:
                                pass
                        
                        print("[TTS STARTUP] Initialization sound complete!")
                        
                        # Extra wait to ensure sound is fully done
                        time.sleep(0.5)
                    else:
                        print(f"[TTS STARTUP] Initialization sound not found: {scifi_sound_path}")
                        time.sleep(2.0)  # Wait anyway
                
                else:
                    # Generate startup sound dynamically (SLOW - 5-10 seconds)
                    print("[TTS STARTUP] Generating startup sound...")
                    startup_audio = self._generate_startup_sound()
                    if startup_audio is not None:
                        self._play_audio(startup_audio)
                        print("[TTS STARTUP] Dynamic startup complete!")
                
                # ============================================================
                # AFTER ALL SOUNDS FINISH: Monica says "MJP I'm fully operational"
                # with a digital sequence sound playing simultaneously
                # ============================================================
                print("[TTS STARTUP] Now playing final greeting with sci-fi sounds...")
                time.sleep(0.5)  # Brief pause after initialization sounds
                
                # Generate and play TERMINATOR-style sci-fi sound SIMULTANEOUSLY with speech
                try:
                    if pygame is None:
                        raise RuntimeError("pygame unavailable")
                    if not pygame.mixer.get_init():
                        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                    
                    # Create TERMINATOR-style boot-up sound
                    sample_rate = 44100
                    duration = 3.0  # 3 seconds
                    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
                    
                    # Terminator-style sound: deep bass pulse + metallic sweep + digital chirps
                    terminator_sound = np.zeros_like(t)
                    
                    # 1. Deep bass pulse (like Terminator theme)
                    bass_freq = 40
                    bass = np.sin(2 * np.pi * bass_freq * t) * 0.4
                    bass += np.sin(2 * np.pi * bass_freq * 2 * t) * 0.2  # Harmonic
                    bass_env = np.exp(-t * 0.5) * (1 + 0.3 * np.sin(2 * np.pi * 2 * t))  # Pulsing
                    terminator_sound += bass * bass_env
                    
                    # 2. Metallic sweep (rising frequency)
                    sweep_freq = 200 + 800 * (t / duration) ** 2
                    sweep = np.sin(2 * np.pi * sweep_freq * t) * 0.25
                    sweep += np.sin(2 * np.pi * sweep_freq * 1.5 * t) * 0.1  # Metallic harmonic
                    sweep_env = np.abs(np.sin(np.pi * t / duration)) ** 0.3  # abs() prevents NaN from negative ** fractional
                    terminator_sound += sweep * sweep_env
                    
                    # 3. Digital chirps/glitches
                    for chirp_time in [0.3, 0.6, 1.0, 1.5, 2.0]:
                        chirp_idx = int(chirp_time * sample_rate)
                        chirp_len = int(0.08 * sample_rate)
                        if chirp_idx + chirp_len < len(t):
                            chirp_t = np.linspace(0, 0.08, chirp_len, dtype=np.float32)
                            chirp_freq = 1500 + np.random.randint(0, 1000)
                            chirp = np.sin(2 * np.pi * chirp_freq * chirp_t) * 0.3
                            chirp *= np.exp(-chirp_t * 30)  # Quick decay
                            terminator_sound[chirp_idx:chirp_idx+chirp_len] += chirp
                    
                    # 4. Final confirmation tone (like "system online")
                    conf_start = int(2.2 * sample_rate)
                    conf_len = int(0.6 * sample_rate)
                    conf_t = np.linspace(0, 0.6, conf_len, dtype=np.float32)
                    conf = np.sin(2 * np.pi * 880 * conf_t) * 0.35  # A5
                    conf += np.sin(2 * np.pi * 1100 * conf_t) * 0.25  # C#6
                    conf += np.sin(2 * np.pi * 1320 * conf_t) * 0.15  # E6
                    conf *= np.abs(np.sin(np.pi * conf_t / 0.6)) ** 0.5  # abs() prevents NaN from negative ** fractional
                    terminator_sound[conf_start:conf_start+conf_len] += conf
                    
                    # Normalize
                    max_val = np.abs(terminator_sound).max()
                    if max_val > 0:
                        terminator_sound = terminator_sound / max_val * 0.65
                    
                    # Convert to stereo 16-bit for pygame
                    digital_16bit = (terminator_sound * 32767).astype(np.int16)
                    digital_stereo = np.column_stack([digital_16bit, digital_16bit])
                    
                    # Create pygame sound and play it
                    digital_snd = pygame.sndarray.make_sound(digital_stereo)
                    digital_snd.set_volume(0.7)
                    digital_snd.play()
                    print("[TTS STARTUP] Playing TERMINATOR-style boot sound...")
                except Exception as de:
                    print(f"[TTS STARTUP] Terminator sound error: {de}")
                
                # NOW Monica speaks the final greeting WHILE digital sound plays
                time.sleep(0.2)  # Small delay so beeps start first
                final_greeting = "MJP, I'm fully operational and ready to assist you."
                print(f"[TTS STARTUP] Final greeting: {final_greeting}")
                # Notify progress (line started)
                try:
                    if on_progress:
                        on_progress('tts_line_started', final_greeting)
                except Exception:
                    pass
                audio_data = self._synthesize_piper(final_greeting)
                if audio_data is not None:
                    self._play_audio(audio_data, wait_for_silence=False)
                # Notify progress (line finished)
                try:
                    if on_progress:
                        on_progress('tts_line_finished', final_greeting)
                except Exception:
                    pass
                
                # Wait for any remaining sounds to finish
                time.sleep(0.3)
                while pygame is not None and pygame.mixer.get_busy():
                    time.sleep(0.1)
                
                print("[TTS STARTUP] Complete startup sequence finished!")
                
                # Pre-load XTTS model in background for instant response on first conversation
                self.preload_xtts_model()
                
                # Call completion callback
                if on_complete:
                    on_complete()
                    
            except Exception as e:
                print(f"[TTS STARTUP] Error: {e}")
                import traceback
                traceback.print_exc()
                if on_complete:
                    on_complete()
            finally:
                # Restore anti-barge-in settings after startup finishes
                self.enable_anti_barge_in = prev_anti
                self.stop_on_user_speech = prev_stop_on_speech
                # CRITICAL: Resume STT after TTS completes (with cooldown)
                self._resume_stt(delay_ms=500)
        
        # Start in background thread
        import threading
        thread = threading.Thread(target=startup_thread, daemon=True)
        thread.start()
    
    def _synthesize(self, text: str, use_xtts_override: Optional[bool] = None) -> Optional[np.ndarray]:
        """Synthesize text to audio."""
        effective_use_xtts = self.use_monica_tts if use_xtts_override is None else bool(use_xtts_override)
        print(f"[TTS] _synthesize called with: '{text[:60]}...' (use_monica_tts={effective_use_xtts})")
        
        # Try MonicaTTS (trained XTTS) first if enabled
        if effective_use_xtts:
            print("[TTS] Attempting MonicaTTS...")
            result = self._synthesize_monica_xtts(text)
            if result is not None:
                print(f"[TTS] MonicaTTS success: {len(result)} samples")
                return result
            print("[TTS] MonicaTTS failed, falling back to Piper")
        
        # Fallback to configured engine
        print(f"[TTS] Using fallback engine: {self.engine_type}")
        if self.engine_type == 'coqui':
            return self._synthesize_coqui(text)
        elif self.engine_type == 'piper':
            return self._synthesize_piper(text)
        else:
            return self._synthesize_system(text)
    
    def _synthesize_monica_xtts(self, text: str) -> Optional[np.ndarray]:
        """Synthesize using MonicaTTS (trained XTTS with your voice)."""
        try:
            monica_tts = get_monica_tts()
            if monica_tts is None:
                return None
            
            print(f"[MONICA XTTS] Synthesizing with trained voice: {text[:50]}...")
            
            # Synthesize to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                temp_path = f.name
            
            # Skip effects for faster response (effects add ~500ms+ latency)
            result_path = monica_tts.synthesize(text, output_path=temp_path, apply_effects=False)
            if result_path is None:
                return None
            
            # Load the audio
            import wave
            with wave.open(result_path, 'rb') as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                audio_bytes = wf.readframes(n_frames)
            
            # Convert to numpy
            if sampwidth == 2:
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
            
            # Handle stereo
            if n_channels == 2:
                audio_data = audio_data.reshape(-1, 2).mean(axis=1)
            
            self.sample_rate = framerate
            
            # Clean up temp file
            try:
                import os
                os.unlink(temp_path)
            except:
                pass
            
            print(f"[MONICA XTTS] Synthesized {len(audio_data)} samples at {self.sample_rate}Hz")
            return audio_data
            
        except Exception as e:
            print(f"[MONICA XTTS] Synthesis error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _synthesize_coqui(self, text: str) -> Optional[np.ndarray]:
        """Synthesize using Coqui TTS."""
        try:
            if not hasattr(self, 'coqui_tts') or self.coqui_tts is None:
                print("[TTS] Coqui TTS not initialized")
                return None
            
            # Synthesize
            print(f"[COQUI TTS] Synthesizing: {text[:50]}...")
            wav = self.coqui_tts.tts(text=text)
            
            # Convert to numpy array
            audio_data = np.array(wav, dtype=np.float32)
            
            # Get actual sample rate from Coqui
            if hasattr(self.coqui_tts, 'synthesizer') and self.coqui_tts.synthesizer:
                self.sample_rate = self.coqui_tts.synthesizer.output_sample_rate
                print(f"[COQUI TTS] Sample rate: {self.sample_rate}")
            
            # Apply sci-fi echo effect
            audio_data = self._apply_scifi_echo(audio_data)
            
            print(f"[COQUI TTS] Synthesized {len(audio_data)} samples at {self.sample_rate}Hz")
            return audio_data
            
        except Exception as e:
            print(f"[COQUI TTS] Synthesis error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _synthesize_piper(self, text: str) -> Optional[np.ndarray]:
        """Synthesize using Piper TTS."""
        try:
            # CRITICAL: Full text normalization for Piper
            # Piper/espeak-ng reads digits individually, so we MUST convert ALL numbers
            import re
            import num2words
            
            print(f"[PIPER] Input text: '{text}'")
            
            # 1. Convert ordinals FIRST (20th -> twentieth, 1st -> first)
            def ordinal_to_words(match):
                num = int(match.group(1))
                try:
                    result = num2words.num2words(num, to='ordinal')
                    print(f"[PIPER] Ordinal: {match.group(0)} -> {result}")
                    return result
                except:
                    return match.group(0)
            
            text = re.sub(r'\b(\d+)(st|nd|rd|th)\b', ordinal_to_words, text, flags=re.IGNORECASE)
            
            # 2. Convert ALL 4-digit years (1000-2099) to spoken form
            def year_to_words(match):
                year = int(match.group(0))
                try:
                    result = num2words.num2words(year, to='year')
                    print(f"[PIPER] Year: {year} -> {result}")
                    return result
                except:
                    return match.group(0)
            
            # Match years from 1000-2099
            text = re.sub(r'\b(1\d{3}|20\d{2})\b', year_to_words, text)
            
            # 3. Fix spaced digits (like "6 6" -> "66")
            # This happens when AI outputs numbers with spaces
            # Must run multiple times to catch all patterns
            for _ in range(5):  # Run multiple passes
                text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)
            
            # 4. Convert ALL remaining numbers to words
            def num_to_words(match):
                num_str = match.group(0)
                try:
                    num = int(num_str)
                    # Use 'year' format for 4-digit numbers that look like years
                    if 1000 <= num <= 2099:
                        result = num2words.num2words(num, to='year')
                    else:
                        result = num2words.num2words(num)
                    print(f"[PIPER] Number: {num} -> {result}")
                    return result
                except:
                    return num_str
            
            # Convert any remaining digits
            text = re.sub(r'\b\d+\b', num_to_words, text)
            
            # 4. Remove punctuation that causes pauses
            text = text.replace('. I ', ' I ')
            text = text.replace(', I ', ' I ')
            text = text.replace('!', '').replace('?', '')
            
            # 5. Clean up
            text = re.sub(r'\s+', ' ', text).strip()
            
            print(f"[PIPER] Final text: '{text}'")
            
            # Collect audio chunks from Piper
            audio_chunks = []
            
            # For multi-speaker models, use speaker config
            if self.engine is None:
                print("Piper engine not initialized")
                return None

            engine_any: Any = self.engine
            if hasattr(self, 'speaker_id') and self.speaker_id is not None and engine_any.config.num_speakers > 1:
                from piper.config import SynthesisConfig
                syn_config = SynthesisConfig(speaker_id=self.speaker_id)
                for chunk in engine_any.synthesize(text, syn_config):
                    audio_chunks.append(chunk.audio_float_array)
            else:
                # Single speaker model - no config needed
                for chunk in engine_any.synthesize(text):
                    audio_chunks.append(chunk.audio_float_array)
            
            # Combine all chunks
            if audio_chunks:
                audio_data = np.concatenate(audio_chunks)
                
                # Apply sci-fi echo effect for elegant spaceship voice
                audio_data = self._apply_scifi_echo(audio_data)
                
                print(f"Piper synthesized {len(audio_data)} samples (with sci-fi echo)")
                return audio_data
            else:
                print("Piper returned no audio")
                return None
            
        except Exception as e:
            print(f"Piper synthesis error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _synthesize_system(self, text: str) -> Optional[np.ndarray]:
        """Synthesize using system TTS."""
        try:
            # System TTS plays directly - doesn't return audio data
            # Create a new engine instance for thread safety
            import pyttsx3  # type: ignore[import-not-found]
            engine = pyttsx3.init()
            
            # Configure voice
            voices = engine.getProperty('voices')
            for voice in voices:
                if 'zira' in voice.name.lower() or 'female' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            
            engine.setProperty('rate', 175)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            return None
            
        except Exception as e:
            print(f"System TTS error: {e}")
            return None
    
    def _play_audio(self, audio_data: np.ndarray, wait_for_silence: bool = True):
        """Play synthesized audio with interrupt support."""
        if audio_data is None:
            return
        
        # Helper to attempt pygame-based playback as a robust fallback
        def _play_with_pygame(a: np.ndarray, sr: int) -> bool:
            if not PYGAME_AVAILABLE:
                return False
            try:
                # Initialize mixer if needed
                if pygame is None:
                    return False
                mix_init = pygame.mixer.get_init()
                if not mix_init:
                    pygame.mixer.init(frequency=sr, size=-16, channels=1, buffer=512)
                    mix_freq = sr
                else:
                    mix_freq = mix_init[0] if isinstance(mix_init, tuple) else sr
                # Convert float32 [-1,1] to int16
                af = np.clip(a.astype(np.float32, copy=False), -1.0, 1.0)
                # Resample to mixer frequency if needed
                if mix_freq != sr and len(af) > 0:
                    try:
                        import numpy as _np
                        x_old = _np.linspace(0.0, 1.0, num=len(af), dtype=_np.float32)
                        x_new = _np.linspace(0.0, 1.0, num=int(len(af) * (mix_freq / float(sr))) or 1, dtype=_np.float32)
                        af = _np.interp(x_new, x_old, af).astype(_np.float32)
                    except Exception:
                        pass
                ai16 = (af * 32767.0).astype(np.int16)
                snd = pygame.sndarray.make_sound(ai16)
                ch = snd.play()
                if ch is None:
                    return False
                duration = len(ai16) / float(mix_freq)
                print(f"[TTS] (pygame) Playing audio: {len(ai16)} samples at {mix_freq}Hz, duration: {duration:.2f}s")
                # Wait until done or interrupted
                check_interval = 0.05
                elapsed = 0.0
                total_wait = duration + 0.1
                while elapsed < total_wait and not self.stop_event.is_set():
                    if not ch.get_busy():
                        break
                    time.sleep(check_interval)
                    elapsed += check_interval
                if self.stop_event.is_set():
                    try:
                        ch.stop()
                    except Exception:
                        pass
                    print("[TTS] (pygame) Audio playback interrupted")
                else:
                    print(f"[TTS] (pygame) Audio playback complete ({duration:.2f}s)")
                return True
            except Exception as e:
                print(f"[TTS] Pygame playback error: {e}")
                return False

        if SOUNDDEVICE_AVAILABLE:
            try:
                # Get sample rate
                sample_rate = getattr(self, 'sample_rate', 22050)
                # Preprocess audio to avoid initial pause: trim leading silence and add short fade-in
                audio_data = self._preprocess_playback_audio(audio_data, sample_rate)

                # Anti-barge-in: wait for brief silence before starting
                # IMPORTANT: add a MAX WAIT so we never hang forever if
                # the input-level detector thinks the user is always speaking.
                if wait_for_silence and self.enable_anti_barge_in and self.is_user_speaking_callback:
                    start_wait = time.time()
                    silence_needed = self.required_silence_ms / 1000.0
                    silent_for = 0.0
                    check_interval = 0.05
                    max_wait = 2.0  # seconds - hard cap to avoid long lag
                    while True:
                        if self.stop_event.is_set():
                            return
                        speaking = False
                        try:
                            speaking = bool(self.is_user_speaking_callback())
                        except Exception:
                            speaking = False
                        if speaking:
                            silent_for = 0.0
                        else:
                            silent_for += check_interval
                        now = time.time()
                        # Start speaking either when we've had enough silence
                        # OR when we've waited too long (noisy room / false positives).
                        if silent_for >= silence_needed or (now - start_wait) >= max_wait:
                            if (now - start_wait) >= max_wait:
                                print("[TTS] Anti-barge-in timeout reached, speaking anyway")
                            break
                        time.sleep(check_interval)

                # Get default output device
                if sd is None:
                    raise RuntimeError("sounddevice unavailable")
                default_device = sd.default.device[1]  # Output device
                duration = len(audio_data) / sample_rate
                print(f"Playing audio: {len(audio_data)} samples at {sample_rate}Hz, duration: {duration:.2f}s (device: {default_device})")
                
                # Play audio (non-blocking) - use default output device
                sd.play(audio_data, samplerate=sample_rate, blocking=False)
                
                # IMPORTANT: On Windows, sd.wait() cuts audio short (GitHub issue #283)
                # Instead, calculate exact duration and use time.sleep() with padding
                # Add 100ms padding to ensure full playback
                total_wait = duration + 0.1
                
                # Wait for playback but check for stop frequently
                check_interval = 0.05  # Check every 50ms
                elapsed = 0
                speaking_elapsed = 0.0
                # Require a bit more continuous speech before we interrupt Monica
                # This avoids cutting her off due to background noise.
                required_speaking_to_stop = 1.5  # INCREASED: Prevent premature cutoffs (was 0.8)
                
                while elapsed < total_wait and not self.stop_event.is_set():
                    # If user starts speaking while we are talking, optionally stop
                    if self.enable_anti_barge_in and self.stop_on_user_speech and self.is_user_speaking_callback:
                        try:
                            if bool(self.is_user_speaking_callback()):
                                speaking_elapsed += check_interval
                            else:
                                speaking_elapsed = 0.0
                            if speaking_elapsed >= required_speaking_to_stop:
                                sd.stop()
                                print("Audio playback stopped due to user speech")
                                break
                        except Exception:
                            pass
                    time.sleep(check_interval)
                    elapsed += check_interval
                
                # If stopped early, stop the audio
                if self.stop_event.is_set():
                    sd.stop()
                    print("Audio playback interrupted")
                else:
                    print(f"Audio playback complete ({duration:.2f}s)")
                    
            except Exception as e:
                print(f"Audio playback error: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to pygame playback if available
                try:
                    sample_rate = getattr(self, 'sample_rate', 22050)
                    if _play_with_pygame(audio_data, sample_rate):
                        return
                except Exception:
                    pass
        else:
            # No sounddevice; try pygame fallback immediately
            sample_rate = getattr(self, 'sample_rate', 22050)
            _play_with_pygame(audio_data, sample_rate)

    def _generate_startup_sound(self) -> Optional[np.ndarray]:
        """Optional dynamic startup sound generator placeholder."""
        return None

    def _preprocess_playback_audio(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """Trim leading silence and apply a short fade-in to avoid initial stutter/pause."""
        if audio is None or len(audio) == 0:
            return audio
        a = audio.astype(np.float32, copy=False)
        # Trim leading silence
        thr = 1e-3  # absolute amplitude threshold
        max_trim = int(0.3 * sample_rate)  # up to 300ms
        start = 0
        for i in range(min(len(a), max_trim)):
            if abs(a[i]) > thr:
                start = i
                break
        if start > 0:
            a = a[start:]
        # Apply short fade-in to first 8ms
        fade_ms = 8
        fade_len = max(1, int(fade_ms / 1000.0 * sample_rate))
        if len(a) > fade_len:
            ramp = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
            a[:fade_len] *= ramp
        return a

    def set_user_speaking_callback(self, fn: Optional[Callable[[], bool]]):
        """Register a callback that returns True if the user is currently speaking."""
        self.is_user_speaking_callback = fn
    
    def stop(self):
        """Stop any ongoing speech."""
        self.stop_event.set()

        if SOUNDDEVICE_AVAILABLE and sd is not None:
            try:
                sd.stop()
            except Exception:
                pass

        self.is_speaking = False
    
    def wait_until_done(self):
        """Wait for speech to complete."""
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join()
    
    # ==================== Voice Management ====================
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voice models."""
        voices = []
        
        # Check downloaded voices
        if self.voices_dir.exists():
            for item in self.voices_dir.iterdir():
                if item.is_dir():
                    onnx_file = item / f"{item.name}.onnx"
                    if onnx_file.exists():
                        info = self.PIPER_VOICES.get(item.name, {})
                        voices.append({
                            'name': item.name,
                            'downloaded': True,
                            **info
                        })
                elif item.suffix == '.onnx':
                    name = item.stem
                    info = self.PIPER_VOICES.get(name, {})
                    voices.append({
                        'name': name,
                        'downloaded': True,
                        **info
                    })
        
        # Add available voices that aren't downloaded
        for name, info in self.PIPER_VOICES.items():
            if not any(v['name'] == name for v in voices):
                voices.append({
                    'name': name,
                    'downloaded': False,
                    **info
                })
        
        return voices
    
    def set_voice(self, voice_name: str) -> bool:
        """Set the current voice model."""
        model_path = self._get_voice_model_path(voice_name)
        
        if model_path is None or not model_path.exists():
            # Try to download
            if not self._download_voice_model(voice_name):
                return False
            model_path = self._get_voice_model_path(voice_name)
        
        if model_path and model_path.exists():
            try:
                from piper import PiperVoice
                self.engine = PiperVoice.load(str(model_path))
                self.current_voice = voice_name
                print(f"Voice changed to: {voice_name}")
                return True
            except Exception as e:
                print(f"Error loading voice: {e}")
                return False
        
        return False
    
    def set_speed(self, speed: float):
        """Set speech speed (0.5 to 2.0)."""
        self.speed = max(0.5, min(2.0, speed))
    
    def set_pitch(self, pitch: float):
        """Set speech pitch (0.5 to 2.0)."""
        self.pitch = max(0.5, min(2.0, pitch))
    
    # ==================== Callbacks ====================
    
    def register_start_callback(self, callback: Callable[[str], None]):
        """Register callback for speech start."""
        if callback not in self.start_callbacks:
            self.start_callbacks.append(callback)
    
    def unregister_start_callback(self, callback: Callable[[str], None]):
        """Unregister start callback."""
        if callback in self.start_callbacks:
            self.start_callbacks.remove(callback)
    
    def register_end_callback(self, callback: Callable[[str], None]):
        """Register callback for speech end."""
        if callback not in self.end_callbacks:
            self.end_callbacks.append(callback)
    
    def unregister_end_callback(self, callback: Callable[[str], None]):
        """Unregister end callback."""
        if callback in self.end_callbacks:
            self.end_callbacks.remove(callback)
    
    def register_audio_callback(self, callback: Callable[[np.ndarray], None]):
        """Register callback for synthesized audio."""
        if callback not in self.audio_callbacks:
            self.audio_callbacks.append(callback)
    
    def unregister_audio_callback(self, callback: Callable[[np.ndarray], None]):
        """Unregister audio callback."""
        if callback in self.audio_callbacks:
            self.audio_callbacks.remove(callback)
