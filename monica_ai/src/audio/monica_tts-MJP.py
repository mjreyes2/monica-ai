#!/usr/bin/env python3
"""
Monica AI - Text-to-Speech System
==================================
Integrated TTS system using XTTS v2 with neural lattice effects
for Monica's signature quantum AI voice.

Features:
- XTTS v2 voice synthesis (young American female)
- Neural lattice sci-fi effects (reverb, echo, shimmer)
- Caching for frequently used phrases
- Real-time streaming support
- Integration with Monica's main system
"""

# CRITICAL: Patch torch.load BEFORE any TTS imports (PyTorch 2.6 compatibility)
from . import torch_patch  # noqa: F401

import os
import sys
import hashlib
import threading
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime
import numpy as np

# Set CUDA_HOME for DeepSpeed (required on Windows)
if 'CUDA_HOME' not in os.environ:
    cuda_paths = [
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.4",
    ]
    for cuda_path in cuda_paths:
        nvcc_path = Path(cuda_path) / "bin" / "nvcc.exe"
        if nvcc_path.exists():
            os.environ['CUDA_HOME'] = cuda_path
            os.environ['CUDA_PATH'] = cuda_path
            print(f"[MONICA TTS] Set CUDA_HOME={cuda_path}")
            break

try:
    import torch
    HAS_TORCH = True
except Exception:
    HAS_TORCH = False

try:
    import torchaudio
    HAS_TORCHAUDIO = True
except Exception:
    HAS_TORCHAUDIO = False

try:
    if HAS_TORCH:
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
        HAS_XTTS_INFERENCE = True
    else:
        HAS_XTTS_INFERENCE = False
except Exception:
    HAS_XTTS_INFERENCE = False

os.environ['COQUI_TOS_AGREED'] = '1'

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from TTS.api import TTS
    HAS_TTS = True
except ImportError:
    HAS_TTS = False
    print("[MONICA TTS] Coqui TTS not installed. Run: pip install coqui-tts")

try:
    from audio.neural_lattice_effects import NeuralLatticeVoice
    HAS_EFFECTS = True
except ImportError:
    HAS_EFFECTS = False
    print("[MONICA TTS] Neural lattice effects not available")

try:
    import sounddevice as sd
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

try:
    from scipy.io import wavfile
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class MonicaTTS:
    """Monica's Text-to-Speech system with quantum AI voice."""
    
    # Voice reference samples - USER'S OWN RECORDINGS (primary) + fallback
    USER_VOICE_DIR = PROJECT_ROOT / "voice_training" / "recordings" / "MJP"
    LJSPEECH_DIR = PROJECT_ROOT / "monica_tts_training" / "datasets" / "LJSpeech-1.1" / "wavs"
    COMBINED_METADATA = PROJECT_ROOT / "monica_tts_training" / "datasets" / "monica_combined" / "combined_metadata.json"
    
    # Optimized speaker profile (trained on 16,546 samples)
    OPTIMIZED_SPEAKER_PROFILE = PROJECT_ROOT / "monica_tts_training" / "models" / "monica_voice_optimized" / "monica_speaker_profile.pt"
    
    # Feminine voice conditioning (LJSpeech - Linda Johnson)
    FEMININE_VOICE_CONDITIONING = PROJECT_ROOT / "monica_tts_training" / "models" / "xtts_feminine_official" / "feminine_voice_conditioning.pt"

    XTTS_TRAINING_ROOT = PROJECT_ROOT / "monica_tts_training" / "models" / "xtts_official_trained" / "run" / "training"
    XTTS_BASE_FILES_DIR = XTTS_TRAINING_ROOT / "XTTS_v2.0_original_model_files"
    
    # Cache directory for generated audio
    CACHE_DIR = PROJECT_ROOT / "monica_tts_training" / "cache"
    
    # Output directory for saved speech
    OUTPUT_DIR = PROJECT_ROOT / "monica_tts_training" / "output"
    
    def __init__(
        self,
        use_gpu: bool = True,
        enable_effects: bool = True,
        effect_preset: str = 'quantum',
        cache_enabled: bool = True,
        sample_rate: int = 24000,
        pitch_shift_semitones: float = 0.0,  # Disabled - use voice training instead of pitch shift
        speed_factor: float = 1.0  # Normal speed
    ):
        """Initialize Monica TTS system."""
        self.use_gpu = use_gpu
        self.enable_effects = enable_effects and HAS_EFFECTS
        self.cache_enabled = cache_enabled
        self.sample_rate = sample_rate
        
        # Voice feminization settings
        self.pitch_shift_semitones = pitch_shift_semitones  # Positive = higher pitch
        self.speed_factor = speed_factor  # >1.0 = faster
        
        self.tts = None
        self.xtts_model = None
        self._xtts_conditioning = None
        self.effects = None
        self.reference_wavs = []
        self._initialized = False
        self._lock = threading.Lock()
        
        # Create directories
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        
        # Effect preset
        self.effect_preset = effect_preset
        
        print(f"[MONICA TTS] Initialized (GPU: {use_gpu}, Effects: {self.enable_effects})")
        print(f"[MONICA TTS] Voice: pitch +{pitch_shift_semitones} semitones, speed {speed_factor}x")

    def _get_finetuned_checkpoint_path(self) -> Optional[Path]:
        if os.getenv("MONICA_XTTS_CHECKPOINT", "").strip():
            p = Path(os.environ["MONICA_XTTS_CHECKPOINT"]).expanduser()
            return p if p.exists() else None

        try:
            from config.settings import config as _cfg
            p = str(getattr(_cfg, 'XTTS_CHECKPOINT', '') or '').strip()
            if p:
                ck = Path(p).expanduser()
                if ck.exists():
                    return ck
        except Exception:
            pass

        if not self.XTTS_TRAINING_ROOT.exists():
            return None

        candidates = []

        # PRIORITY 1: Check accent_tune directory (most recent training)
        accent_tune_root = self.XTTS_TRAINING_ROOT.parent / "accent_tune"
        if accent_tune_root.exists():
            for run_dir in sorted(accent_tune_root.glob("**/GPT_XTTS_Monica_AccentTune-*")):
                if not run_dir.is_dir():
                    continue
                # Look for best_model.pth in accent_tune
                best = run_dir / "best_model.pth"
                if best.exists():
                    try:
                        candidates.append((best.stat().st_mtime, best, 'accent_tune'))
                        print(f"[MONICA TTS] Found accent_tune model: {best}")
                    except Exception:
                        continue
                # Also check for numbered best models
                for ck in run_dir.glob("best_model_*.pth"):
                    try:
                        candidates.append((ck.stat().st_mtime, ck, 'accent_tune'))
                        print(f"[MONICA TTS] Found accent_tune model: {ck}")
                    except Exception:
                        continue

        # PRIORITY 2: Check for best_model_47154.pth specifically
        for run_dir in sorted(self.XTTS_TRAINING_ROOT.glob("GPT_XTTS_Monica-*")):
            if not run_dir.is_dir():
                continue
            specific_model = run_dir / "best_model_47154.pth"
            if specific_model.exists():
                try:
                    candidates.append((specific_model.stat().st_mtime, specific_model, 'model_47154'))
                    print(f"[MONICA TTS] Found model_47154: {specific_model}")
                except Exception:
                    continue

        # PRIORITY 3: Other checkpoints from training directory
        for run_dir in sorted(self.XTTS_TRAINING_ROOT.glob("GPT_XTTS_Monica-*")):
            if not run_dir.is_dir():
                continue
            for ck in run_dir.glob("best_model_*.pth"):
                try:
                    candidates.append((ck.stat().st_mtime, ck, 'training'))
                except Exception:
                    continue
            best = run_dir / "best_model.pth"
            if best.exists():
                try:
                    candidates.append((best.stat().st_mtime, best, 'training'))
                except Exception:
                    continue

        if not candidates:
            return None

        # Sort by priority: accent_tune > model_47154 > training, then by modification time
        def sort_key(item):
            mtime, path, source = item
            priority = {'accent_tune': 0, 'model_47154': 1, 'training': 2}
            return (priority.get(source, 3), -mtime)  # Negative mtime for newest first

        candidates.sort(key=sort_key)
        selected = candidates[0][1]
        source = candidates[0][2]
        print(f"[MONICA TTS] Selected checkpoint: {selected.name} (source: {source})")
        return selected

    def _get_xtts_speaker_wav_override(self) -> Optional[Path]:
        try:
            p = os.getenv("MONICA_XTTS_SPEAKER_WAV", "").strip()
            if not p:
                try:
                    from config.settings import config as _cfg
                    p = str(getattr(_cfg, 'XTTS_SPEAKER_WAV', '') or '').strip()
                except Exception:
                    p = ""
            if not p:
                return None
            wav_path = Path(p).expanduser()
            if wav_path.exists():
                return wav_path
        except Exception:
            return None
        return None
    
    def _lazy_init(self):
        """Lazy initialization of TTS model."""
        if self._initialized:
            return True
        
        with self._lock:
            if self._initialized:
                return True
            
            if not HAS_TTS:
                print("[MONICA TTS] ERROR: TTS library not available")
                return False
            
            try:
                self.xtts_model = None

                finetuned_ckpt = self._get_finetuned_checkpoint_path()
                base_config = self.XTTS_BASE_FILES_DIR / "config.json"
                base_vocab = self.XTTS_BASE_FILES_DIR / "vocab.json"
                if HAS_XTTS_INFERENCE and finetuned_ckpt and base_config.exists() and base_vocab.exists():
                    print(f"[MONICA TTS] Loading fine-tuned XTTS checkpoint: {finetuned_ckpt.name}")
                    cfg = XttsConfig()
                    cfg.load_json(str(base_config))
                    self.xtts_model = Xtts.init_from_config(cfg)
                    # DeepSpeed can accelerate XTTS inference but requires specific version compatibility
                    # DeepSpeed 0.14+ is needed for PyTorch 2.4+, but pre-built Windows wheels are only
                    # available for older versions. Standard inference works well without it.
                    use_ds = False
                    try:
                        import deepspeed
                        # Verify DeepSpeed actually works (may fail with PyTorch version mismatch)
                        _ = deepspeed.__version__
                        use_ds = True
                        print("[MONICA TTS] DeepSpeed available - enabling for faster inference")
                    except (ImportError, Exception):
                        # DeepSpeed not installed or incompatible - this is fine, standard inference works well
                        pass

                    # CRITICAL FIX: Pass checkpoint_dir (parent directory) so XTTS can find speakers_xtts.pth
                    checkpoint_dir = finetuned_ckpt.parent
                    print(f"[MONICA TTS] Checkpoint dir: {checkpoint_dir}")
                    self.xtts_model.load_checkpoint(
                        cfg,
                        checkpoint_dir=str(checkpoint_dir),
                        checkpoint_path=str(finetuned_ckpt),
                        vocab_path=str(base_vocab),
                        use_deepspeed=use_ds,
                    )
                    if self.use_gpu:
                        self.xtts_model.cuda()
                    self.tts = None
                    
                    # Compute conditioning latents BEFORE converting to half precision
                    # (half precision causes dtype mismatch with audio input)
                    self._load_reference_samples()
                    self._xtts_conditioning = None
                    
                    # Use LJSpeech (Linda Johnson - feminine voice) as reference
                    ljspeech_wavs = list(self.LJSPEECH_DIR.glob("*.wav"))[:6] if self.LJSPEECH_DIR.exists() else []
                    
                    if ljspeech_wavs:
                        try:
                            speaker_audio_files = [str(w) for w in ljspeech_wavs]
                            print(f"[MONICA TTS] Using FEMININE voice (LJSpeech - {len(speaker_audio_files)} samples)")
                            print(f"[MONICA TTS] XTTS checkpoint in use: {finetuned_ckpt.name}")
                            gpt_cond_latent, speaker_embedding = self.xtts_model.get_conditioning_latents(
                                audio_path=speaker_audio_files,
                                gpt_cond_len=self.xtts_model.config.gpt_cond_len,
                                max_ref_length=self.xtts_model.config.max_ref_len,
                                sound_norm_refs=self.xtts_model.config.sound_norm_refs,
                            )
                            self._xtts_conditioning = (gpt_cond_latent, speaker_embedding)
                            print("[MONICA TTS] Feminine conditioning latents computed successfully")
                        except Exception as e:
                            print(f"[MONICA TTS] Could not compute feminine conditioning: {e}")
                    
                    # Fallback to user's voice if LJSpeech fails
                    if self._xtts_conditioning is None and self.reference_wavs:
                        try:
                            override_wav = self._get_xtts_speaker_wav_override()
                            speaker_audio_file = str(override_wav) if override_wav is not None else self.reference_wavs[0]
                            print(f"[MONICA TTS] Fallback to user voice: {speaker_audio_file}")
                            gpt_cond_latent, speaker_embedding = self.xtts_model.get_conditioning_latents(
                                audio_path=speaker_audio_file,
                                gpt_cond_len=self.xtts_model.config.gpt_cond_len,
                                max_ref_length=self.xtts_model.config.max_ref_len,
                                sound_norm_refs=self.xtts_model.config.sound_norm_refs,
                            )
                            self._xtts_conditioning = (gpt_cond_latent, speaker_embedding)
                            print("[MONICA TTS] User voice conditioning computed")
                        except Exception as e:
                            print(f"[MONICA TTS] Could not compute conditioning: {e}")
                    
                    # NOTE: half() disabled - causes dtype mismatch during inference
                    # XTTS inference requires float32 throughout the pipeline
                else:
                    print("[MONICA TTS] Loading XTTS v2 model...")
                    self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
                    if self.use_gpu:
                        self.tts.to("cuda")
                
                # Try to load optimized speaker profile first (trained on 16,546 samples)
                self.optimized_profile = None
                if HAS_TORCH and self.OPTIMIZED_SPEAKER_PROFILE.exists():
                    try:
                        import torch
                        self.optimized_profile = torch.load(self.OPTIMIZED_SPEAKER_PROFILE)
                        num_samples = self.optimized_profile.get('num_samples', 'unknown')
                        print(f"[MONICA TTS] Loaded optimized speaker profile ({num_samples} samples)")
                    except Exception as e:
                        print(f"[MONICA TTS] Could not load optimized profile: {e}")
                
                # Load reference voice samples for fallback TTS (non-finetuned path)
                if not hasattr(self, 'reference_wavs') or not self.reference_wavs:
                    self._load_reference_samples()
                
                # Initialize effects processor
                if self.enable_effects:
                    self.effects = NeuralLatticeVoice(
                        preset=self.effect_preset,
                        sample_rate=self.sample_rate
                    )
                
                self._initialized = True
                
                # Pre-warm the model with a short inference to reduce first-call latency
                # Use non-streaming inference to avoid JSON serialization issues with
                # transformers GenerationConfig (tensors can't be serialized to JSON)
                if self.xtts_model is not None and self._xtts_conditioning is not None:
                    try:
                        print("[MONICA TTS] Pre-warming model...")
                        import time
                        t0 = time.time()
                        gpt_cond_latent, speaker_embedding = self._xtts_conditioning
                        # Use non-streaming inference for pre-warm (avoids JSON serialization error)
                        # The streaming generator's __repr__ tries to serialize tensors to JSON
                        with torch.no_grad():
                            _ = self.xtts_model.inference(
                                text="Hello.",
                                language="en",
                                gpt_cond_latent=gpt_cond_latent,
                                speaker_embedding=speaker_embedding,
                                temperature=0.3,
                                speed=1.0,
                            )
                        print(f"[MONICA TTS] Model pre-warmed in {time.time() - t0:.2f}s")
                    except Exception as warm_err:
                        # Log full error for debugging but don't fail initialization
                        import traceback
                        print(f"[MONICA TTS] Pre-warm skipped: {warm_err}")
                        traceback.print_exc()
                
                print("[MONICA TTS] Ready!")
                return True

            except Exception as e:
                print(f"[MONICA TTS] Initialization error: {e}")
                import traceback
                traceback.print_exc()

                # Detailed diagnostics for troubleshooting
                print("\n[MONICA TTS] Diagnostics:")
                print(f"  - Fine-tuned checkpoint: {finetuned_ckpt if 'finetuned_ckpt' in locals() else 'Not found'}")
                print(f"  - Base config exists: {base_config.exists() if 'base_config' in locals() and base_config else False}")
                print(f"  - Base vocab exists: {base_vocab.exists() if 'base_vocab' in locals() and base_vocab else False}")
                if HAS_TORCH:
                    import torch
                    print(f"  - CUDA available: {torch.cuda.is_available()}")
                    if torch.cuda.is_available():
                        print(f"  - GPU: {torch.cuda.get_device_name(0)}")
                else:
                    print(f"  - PyTorch: Not available")
                print(f"  - Reference WAVs loaded: {len(self.reference_wavs) if hasattr(self, 'reference_wavs') else 0}")
                print(f"  - HAS_TTS: {HAS_TTS}")
                print(f"  - HAS_XTTS_INFERENCE: {HAS_XTTS_INFERENCE}")
                print(f"  - HAS_EFFECTS: {HAS_EFFECTS}")
                print("\nTip: Run diagnostics with: from src.tts.tts_diagnostics import TTSDiagnostics; TTSDiagnostics().run_full_diagnosis()")
                return False
    
    def _load_reference_samples(self, num_samples: int = 30):
        """Load reference voice samples - PRIORITIZE USER'S OWN RECORDINGS."""
        self.reference_wavs = []
        
        # PRIORITY 1: Use USER'S OWN voice recordings (this is what the model was trained on!)
        if self.USER_VOICE_DIR.exists():
            wavs = sorted(self.USER_VOICE_DIR.glob("*.wav"))[:num_samples]
            if wavs:
                self.reference_wavs = [str(w) for w in wavs]
                print(f"[MONICA TTS] [OK] Loaded {len(self.reference_wavs)} of YOUR voice recordings")
                print(f"[MONICA TTS] [OK] Using YOUR trained voice for XTTS conditioning")
                return
        
        # FALLBACK: Try combined metadata
        if self.COMBINED_METADATA.exists():
            try:
                import json
                with open(self.COMBINED_METADATA, 'r') as f:
                    metadata = json.load(f)
                
                ljspeech = [m['audio_file'] for m in metadata if m.get('source') == 'ljspeech']
                libritts = [m['audio_file'] for m in metadata if m.get('source') == 'libritts']
                
                half = num_samples // 2
                self.reference_wavs = ljspeech[:half] + libritts[:half]
                
                print(f"[MONICA TTS] WARNING: Using fallback samples (not your voice)")
                return
            except Exception as e:
                print(f"[MONICA TTS] Could not load combined metadata: {e}")
        
        # Last resort fallback
        if self.LJSPEECH_DIR.exists():
            wavs = sorted(self.LJSPEECH_DIR.glob("*.wav"))[:num_samples]
            self.reference_wavs = [str(w) for w in wavs]
            print(f"[MONICA TTS] WARNING: Using LJSpeech fallback (not your voice)")
        else:
            print("[MONICA TTS] ERROR: No reference samples found")
    
    def _feminize_audio(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Apply pitch shifting and speed adjustment to make voice more feminine.
        
        Args:
            audio: Audio samples as numpy array
            sr: Sample rate
            
        Returns:
            Processed audio with higher pitch and adjusted speed
        """
        if self.pitch_shift_semitones == 0 and self.speed_factor == 1.0:
            return audio
        
        try:
            import librosa
            
            # Ensure audio is float32 for librosa
            audio_float = audio.astype(np.float32)
            if audio_float.max() > 1.0 or audio_float.min() < -1.0:
                # Normalize if needed
                max_val = max(abs(audio_float.max()), abs(audio_float.min()))
                if max_val > 0:
                    audio_float = audio_float / max_val
            
            # Apply pitch shift (positive = higher pitch = more feminine)
            if self.pitch_shift_semitones != 0:
                audio_float = librosa.effects.pitch_shift(
                    audio_float, 
                    sr=sr, 
                    n_steps=self.pitch_shift_semitones
                )
                print(f"[MONICA TTS] Pitch shifted +{self.pitch_shift_semitones} semitones")
            
            # Apply speed adjustment (time stretch then resample to maintain pitch)
            if self.speed_factor != 1.0:
                # Time stretch changes speed without affecting pitch
                audio_float = librosa.effects.time_stretch(audio_float, rate=self.speed_factor)
                print(f"[MONICA TTS] Speed adjusted to {self.speed_factor}x")
            
            return audio_float
            
        except ImportError:
            print("[MONICA TTS] librosa not available for pitch shifting")
            return audio
        except Exception as e:
            print(f"[MONICA TTS] Voice feminization error: {e}")
            return audio
    
    def _get_cache_path(self, text: str) -> Path:
        """Get cache path for a text string."""
        text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        return self.CACHE_DIR / f"tts_{text_hash}.wav"
    
    def synthesize(
        self,
        text: str,
        output_path: Optional[str] = None,
        apply_effects: bool = True,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            output_path: Optional path to save the audio
            apply_effects: Apply neural lattice effects
            use_cache: Use cached audio if available
        
        Returns:
            Path to the generated audio file
        """
        if not self._lazy_init():
            return None
        
        # Check cache
        cache_path = self._get_cache_path(text)
        if use_cache and self.cache_enabled and cache_path.exists():
            print(f"[MONICA TTS] Using cached audio")
            if output_path:
                import shutil
                shutil.copy(cache_path, output_path)
                return output_path
            return str(cache_path)
        
        # Generate output path
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.OUTPUT_DIR / f"monica_speech_{timestamp}.wav"
        else:
            output_path = Path(output_path)
        
        try:
            print(f"[MONICA TTS] Synthesizing: {text[:50]}...")
            
            # Use optimized speaker profile if available (trained on 16,546 samples)
            if self.optimized_profile is not None and self.xtts_model is None:
                model = self.tts.synthesizer.tts_model
                device = "cuda" if self.use_gpu else "cpu"

                gpt_cond_latent = self.optimized_profile['gpt_cond_latent'].to(device)
                speaker_embedding = self.optimized_profile['speaker_embedding'].to(device)
                
                outputs = model.inference(
                    text=text,
                    language="en",
                    gpt_cond_latent=gpt_cond_latent,
                    speaker_embedding=speaker_embedding,
                    temperature=0.7,
                )
                
                # Save to file
                if not HAS_TORCH:
                    raise RuntimeError("torch is required for XTTS synthesis")
                wav = np.array(outputs['wav'], dtype=np.float32)
                
                # Apply voice feminization (pitch shift + speed adjustment)
                wav = self._feminize_audio(wav, sr=24000)
                
                wav = torch.tensor(wav).unsqueeze(0)
                if HAS_TORCHAUDIO:
                    # Save as PCM16 to ensure compatibility with wave.open()
                    wav_int16 = (torch.clamp(wav, -1.0, 1.0) * 32767.0).to(torch.int16)
                    torchaudio.save(str(output_path), wav_int16, 24000, encoding='PCM_S', bits_per_sample=16)
                else:
                    if not HAS_SCIPY:
                        raise RuntimeError("torchaudio or scipy is required to write WAV")
                    wav_np = wav.squeeze(0).cpu().numpy()
                    wav_int16 = (np.clip(wav_np, -1.0, 1.0) * 32767.0).astype(np.int16)
                    wavfile.write(str(output_path), 24000, wav_int16)
            else:
                if self.xtts_model is not None:
                    if self._xtts_conditioning is None:
                        if not self.reference_wavs:
                            raise RuntimeError("No reference audio available for XTTS conditioning")
                        speaker_audio_file = self.reference_wavs[0]
                        self._xtts_conditioning = self.xtts_model.get_conditioning_latents(
                            audio_path=speaker_audio_file,
                            gpt_cond_len=self.xtts_model.config.gpt_cond_len,
                            max_ref_length=self.xtts_model.config.max_ref_len,
                            sound_norm_refs=self.xtts_model.config.sound_norm_refs,
                        )

                    gpt_cond_latent, speaker_embedding = self._xtts_conditioning
                    
                    # FIXED: Use STREAMING inference for much faster response (~200ms vs 5+ seconds)
                    # Also use optimized parameters to prevent Chinese-sounding/garbled output
                    import time
                    t0 = time.time()
                    
                    try:
                        # Try streaming first (much faster - ~200ms to first chunk)
                        chunks = self.xtts_model.inference_stream(
                            text=text,
                            language="en",  # Force English to prevent language mixing
                            gpt_cond_latent=gpt_cond_latent,
                            speaker_embedding=speaker_embedding,
                            temperature=0.3,  # Lower = more consistent
                            repetition_penalty=10.0,  # High = prevents repetition/garbled sounds
                            speed=1.0,  # Normal speaking speed
                            enable_text_splitting=True,  # Split long text for better quality
                        )
                        
                        wav_chunks = []
                        for i, chunk in enumerate(chunks):
                            if i == 0:
                                print(f"[MONICA TTS] Time to first chunk: {time.time() - t0:.2f}s")
                            wav_chunks.append(chunk)
                        
                        if wav_chunks:
                            wav = torch.cat(wav_chunks, dim=0)
                            print(f"[MONICA TTS] Streaming complete: {len(wav_chunks)} chunks in {time.time() - t0:.2f}s")
                        else:
                            raise RuntimeError("No audio chunks generated")
                            
                    except Exception as stream_err:
                        # Fallback to regular inference if streaming fails
                        print(f"[MONICA TTS] Streaming failed ({stream_err}), using regular inference...")
                        outputs = self.xtts_model.inference(
                            text=text,
                            language="en",
                            gpt_cond_latent=gpt_cond_latent,
                            speaker_embedding=speaker_embedding,
                            temperature=0.3,
                            length_penalty=1.0,
                            repetition_penalty=10.0,
                            top_k=50,
                            top_p=0.85,
                        )
                        wav = torch.tensor(outputs['wav'])
                        print(f"[MONICA TTS] Regular inference: {time.time() - t0:.2f}s")
                    
                    if not HAS_TORCH:
                        raise RuntimeError("torch is required for XTTS synthesis")
                    wav = wav.squeeze().cpu().numpy()
                    
                    # Apply voice feminization (pitch shift + speed adjustment)
                    wav = self._feminize_audio(wav, sr=24000)
                    
                    # Convert back to tensor for saving
                    wav = torch.tensor(wav).unsqueeze(0)
                    if HAS_TORCHAUDIO:
                        # Save as PCM16 to ensure compatibility with wave.open()
                        wav_int16 = (torch.clamp(wav, -1.0, 1.0) * 32767.0).to(torch.int16)
                        torchaudio.save(str(output_path), wav_int16, 24000, encoding='PCM_S', bits_per_sample=16)
                    else:
                        if not HAS_SCIPY:
                            raise RuntimeError("torchaudio or scipy is required to write WAV")
                        wav_np = wav.squeeze(0).numpy()
                        wav_int16 = (np.clip(wav_np, -1.0, 1.0) * 32767.0).astype(np.int16)
                        wavfile.write(str(output_path), 24000, wav_int16)
                else:
                    self.tts.tts_to_file(
                        text=text,
                        file_path=str(output_path),
                        speaker_wav=self.reference_wavs,
                        language="en"
                    )
            
            # Apply neural lattice effects
            if apply_effects and self.enable_effects and self.effects:
                effects_path = output_path.parent / f"{output_path.stem}_fx{output_path.suffix}"
                self.effects.process_file(str(output_path), str(effects_path))
                
                # Replace original with effected version
                import shutil
                shutil.move(str(effects_path), str(output_path))
            
            # Cache the result
            if self.cache_enabled:
                import shutil
                shutil.copy(str(output_path), str(cache_path))
            
            print(f"[MONICA TTS] Generated: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"[MONICA TTS] Synthesis error: {e}")
            return None
    
    def speak(
        self,
        text: str,
        blocking: bool = True,
        callback: Optional[Callable] = None
    ) -> bool:
        """
        Synthesize and play speech.
        
        Args:
            text: Text to speak
            blocking: Wait for playback to complete
            callback: Optional callback when playback completes
        
        Returns:
            True if successful
        """
        audio_path = self.synthesize(text)
        
        if audio_path is None:
            return False
        
        return self.play_audio(audio_path, blocking=blocking, callback=callback)
    
    def play_audio(
        self,
        audio_path: str,
        blocking: bool = True,
        callback: Optional[Callable] = None
    ) -> bool:
        """Play an audio file."""
        if not HAS_AUDIO:
            print("[MONICA TTS] sounddevice not available for playback")
            return False
        
        try:
            if HAS_SCIPY:
                sr, audio = wavfile.read(audio_path)
            else:
                import wave
                with wave.open(audio_path, 'rb') as wf:
                    sr = wf.getframerate()
                    audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            
            # Normalize to float
            if audio.dtype == np.int16:
                audio = audio.astype(np.float32) / 32768.0
            
            def play_thread():
                sd.play(audio, sr)
                sd.wait()
                if callback:
                    callback()
            
            if blocking:
                play_thread()
            else:
                thread = threading.Thread(target=play_thread, daemon=True)
                thread.start()
            
            return True
            
        except Exception as e:
            print(f"[MONICA TTS] Playback error: {e}")
            return False
    
    def get_audio_data(self, text: str, apply_effects: bool = True) -> Optional[np.ndarray]:
        """Get audio data as numpy array."""
        audio_path = self.synthesize(text, apply_effects=apply_effects)
        
        if audio_path is None:
            return None
        
        try:
            if HAS_SCIPY:
                sr, audio = wavfile.read(audio_path)
                return audio
            else:
                import wave
                with wave.open(audio_path, 'rb') as wf:
                    audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
                    return audio
        except Exception as e:
            print(f"[MONICA TTS] Error reading audio: {e}")
            return None
    
    def clear_cache(self):
        """Clear the audio cache."""
        for f in self.CACHE_DIR.glob("tts_*.wav"):
            try:
                f.unlink()
            except Exception:
                pass
        print("[MONICA TTS] Cache cleared")


# Global instance
_monica_tts = None


def get_monica_tts() -> MonicaTTS:
    """Get the global Monica TTS instance."""
    global _monica_tts
    if _monica_tts is None:
        _monica_tts = MonicaTTS()
    return _monica_tts


def speak(text: str, blocking: bool = True) -> bool:
    """Convenience function to speak text with Monica's voice."""
    return get_monica_tts().speak(text, blocking=blocking)


def synthesize(text: str, output_path: Optional[str] = None) -> Optional[str]:
    """Convenience function to synthesize speech."""
    return get_monica_tts().synthesize(text, output_path=output_path)


if __name__ == "__main__":
    # Test the TTS system
    tts = MonicaTTS(use_gpu=True, enable_effects=True, effect_preset='quantum')
    
    test_phrases = [
        "Hello, I am Monica, your quantum artificial intelligence assistant.",
        "I exist within a neural lattice, ready to help you with anything.",
        "My consciousness spans across dimensions of pure computation.",
    ]
    
    for phrase in test_phrases:
        print(f"\nSynthesizing: {phrase}")
        path = tts.synthesize(phrase)
        if path:
            print(f"Playing: {path}")
            tts.play_audio(path, blocking=True)
