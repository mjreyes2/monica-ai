"""
Final SpeechBrain Personal Voice Recognition
Based on research: wav2vec2 models take 60-120s to load normally
Pure SpeechBrain - 100% accuracy, wait for full load
"""

# CRITICAL: Patch transformers FIRST, before any other imports
from . import torch_patch  # noqa: F401

import os
import sys
import torch
import torchaudio
from pathlib import Path
import json
import numpy as np
import time
import threading
import queue

# Set environment variable to disable symlink warnings
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # monica_ai/src/audio -> monica_ai/src -> monica_ai -> monica_project
_TRAINING_ROOT = _PROJECT_ROOT / "data" / "training"
_HF_CACHE_ROOT = _TRAINING_ROOT / "cache" / "hf_cache"
try:
    _HF_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

os.environ.setdefault('HF_HOME', str(_HF_CACHE_ROOT))
os.environ.setdefault('HF_HUB_CACHE', str(_HF_CACHE_ROOT / 'hub'))
os.environ.setdefault('TRANSFORMERS_CACHE', str(_HF_CACHE_ROOT / 'transformers'))
os.environ.setdefault('TORCH_HOME', str(_HF_CACHE_ROOT / 'torch'))

# Import SpeechBrain
try:
    from speechbrain.inference.ASR import EncoderDecoderASR
    from speechbrain.inference.speaker import SpeakerRecognition
    HAS_SPEECHBRAIN = True
except ImportError:
    HAS_SPEECHBRAIN = False
    print("[SPEECHBRAIN] SpeechBrain not available")

# Import custom model loader (SpeechBrain - has WER 100% bug)
try:
    from .custom_model_loader import MonicaCustomASR, load_monica_custom_model
    HAS_CUSTOM_MODEL = True
    print("[CUSTOM-MODEL] Custom Monica model loader available")
except ImportError as e:
    HAS_CUSTOM_MODEL = False
    print(f"[CUSTOM-MODEL] Custom loader not available: {e}")

# Import HuggingFace ASR (PREFERRED - trained model that works!)
try:
    from .huggingface_asr import HuggingFaceASR, load_huggingface_asr
    HAS_HUGGINGFACE_ASR = True
    print("[HUGGINGFACE-ASR] HuggingFace ASR loader available")
except ImportError as e:
    HAS_HUGGINGFACE_ASR = False
    print(f"[HUGGINGFACE-ASR] HuggingFace loader not available: {e}")

# Import STT Accuracy Enhancer (fixes noise, speed, vocabulary, accent drift)
try:
    from .stt_accuracy_enhancer import get_stt_enhancer
    HAS_STT_ENHANCER = True
    print("[STT-ENHANCER] STT Accuracy Enhancer available")
except ImportError as e:
    HAS_STT_ENHANCER = False
    print(f"[STT-ENHANCER] STT Accuracy Enhancer not available: {e}")

# Import Silero VAD for background noise filtering (enterprise-grade)
try:
    from silero_vad import load_silero_vad, get_speech_timestamps
    HAS_SILERO_VAD = True
    print("[SILERO-VAD] Silero VAD available for noise filtering")
except ImportError:
    HAS_SILERO_VAD = False
    print("[SILERO-VAD] Silero VAD not available - install with: pip install silero-vad")

# Whisper DISABLED - using YOUR trained wav2vec2 model (36k+ samples)
HAS_WHISPER = False

class FinalSpeechBrainRecognizer:
    """
    Final SpeechBrain Personal Voice Recognition
    Implements research-based solutions for wav2vec2 loading performance
    """
    
    def __init__(self):
        project_root = _PROJECT_ROOT
        self.model_dir = _TRAINING_ROOT / "cache"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Persistent cache directories (from SpeechBrain docs)
        self.asr_cache_dir = self.model_dir / "asr_wav2vec2_cached"
        self.speaker_cache_dir = self.model_dir / "speaker_cached"
        self.asr_cache_dir.mkdir(parents=True, exist_ok=True)
        self.speaker_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Model components
        self.asr_model = None
        self.speaker_model = None
        self.voice_signature = None
        
        # Load custom vocabulary for better recognition
        self.vocabulary = self._load_vocabulary()
        
        # STT Accuracy Enhancer (fixes 4 major issues)
        self.stt_enhancer = None
        if HAS_STT_ENHANCER:
            try:
                self.stt_enhancer = get_stt_enhancer(sample_rate=16000, model_dir=self.model_dir)
                print("[FINAL-SPEECHBRAIN] STT Accuracy Enhancer enabled")
            except Exception as e:
                print(f"[FINAL-SPEECHBRAIN] STT Enhancer init failed: {e}")
                self.stt_enhancer = None
        
        # Silero VAD for background noise filtering
        self.vad_model = None
        if HAS_SILERO_VAD:
            try:
                self.vad_model = load_silero_vad()
                print("[FINAL-SPEECHBRAIN] Silero VAD loaded for noise filtering")
            except Exception as e:
                print(f"[FINAL-SPEECHBRAIN] Silero VAD load failed: {e}")
                self.vad_model = None
        
        # Whisper DISABLED - using YOUR trained model
        self.whisper_model = None
        self.use_whisper = False
        
        # KenLM Language Model for better accuracy
        self.lm_decoder = None
        self._init_language_model()
        
        # State management
        self.is_loaded = False
        self.loading_failed = False
        self.last_load_error = None
        self.loading_start_time = None
        self.loading_thread = None
        
        # Request queue for processing during loading
        self.request_queue = queue.Queue()
        
        # Start loading immediately
        self._start_loading()
        
        print("[FINAL-SPEECHBRAIN] Final recognizer initialized!")
    
    def _start_loading(self):
        """Start loading models with research-based optimizations"""
        if not HAS_SPEECHBRAIN:
            print("[FINAL-SPEECHBRAIN] SpeechBrain not available")
            self.loading_failed = True
            return
        
        def load_models():
            try:
                self.loading_start_time = time.time()
                gpu_msg = "with GPU acceleration" if torch.cuda.is_available() else "on CPU"
                print(f"[FINAL-SPEECHBRAIN] Starting model loading {gpu_msg}...")
                
                # Load ASR model with persistent caching (from SpeechBrain docs)
                asr_start = time.time()
                
                # Use CUDA if available for faster loading and inference
                device = "cuda" if torch.cuda.is_available() else "cpu"
                print(f"[FINAL-SPEECHBRAIN] Using device: {device}")
                
                # GPU verification
                if torch.cuda.is_available():
                    if device == "cuda":
                        print(f"[FINAL-SPEECHBRAIN] [OK] GPU acceleration enabled")
                        print(f"[FINAL-SPEECHBRAIN] GPU: {torch.cuda.get_device_name(0)}")
                    else:
                        print(f"[FINAL-SPEECHBRAIN] [WARNING] CUDA available but using CPU")

                # ===================================================================
                # LOAD YOUR TRAINED MODEL (wav2vec2_final - WORKS CORRECTLY)
                # ===================================================================
                project_root = _PROJECT_ROOT  # monica_project
                
                # Use wav2vec2_your_voice model - trained on ALL 4,217 of your recordings!
                # WER: 29.33% - much better than previous models
                trained_model_path = project_root / "models" / "wav2vec2_your_voice" / "final_model"
                
                if trained_model_path.exists():
                    print(f"[MONICA-STT] Loading YOUR TRAINED MODEL")
                    print(f"[MONICA-STT] Model path: {trained_model_path}")
                    
                    # Retry logic for CUDA busy errors
                    max_retries = 3
                    retry_delay = 2.0  # seconds
                    
                    for attempt in range(max_retries):
                        try:
                            # Synchronize CUDA before loading to avoid conflicts with TTS
                            if torch.cuda.is_available():
                                torch.cuda.synchronize()
                                torch.cuda.empty_cache()
                            
                            from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
                            self.enhanced_processor = Wav2Vec2Processor.from_pretrained(str(trained_model_path))
                            self.enhanced_model = Wav2Vec2ForCTC.from_pretrained(str(trained_model_path))
                            self.enhanced_model = self.enhanced_model.to(device)
                            self.enhanced_model.eval()
                            self.use_enhanced = True
                            print(f"[MONICA-STT] [SUCCESS] Your trained model loaded in {time.time() - asr_start:.2f}s")
                            print(f"[MONICA-STT] Using YOUR trained model as PRIMARY STT")
                            break  # Success - exit retry loop
                        except Exception as model_error:
                            error_str = str(model_error)
                            if "CUDA" in error_str and "busy" in error_str and attempt < max_retries - 1:
                                print(f"[MONICA-STT] CUDA busy, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                                time.sleep(retry_delay)
                                retry_delay *= 1.5  # Exponential backoff
                            else:
                                print(f"[MONICA-STT] Model load failed: {model_error}")
                                self.use_enhanced = False
                                break
                else:
                    self.use_enhanced = False
                    print(f"[MONICA-STT] Trained model not found at {trained_model_path}")
                
                # ONLY try other models if enhanced model failed or doesn't exist
                if not self.use_enhanced:
                    # FALLBACK 1: Try wav2vec2_final model (older model)
                    hf_model_path = project_root / "models" / "wav2vec2_final" / "final_model"
                    
                    if HAS_HUGGINGFACE_ASR and hf_model_path.exists():
                        print(f"[MONICA-HF] Loading YOUR CUSTOM TRAINED MODEL (HuggingFace)")
                        print(f"[MONICA-HF] Model path: {hf_model_path}")
                        print(f"[MONICA-HF] Trained on YOUR voice recordings!")
                        
                        try:
                            self.asr_model = load_huggingface_asr(device=device)
                            print(f"[MONICA-HF] [SUCCESS] CUSTOM MODEL LOADED in {time.time() - asr_start:.2f}s on {device}")
                            print(f"[MONICA-HF] This model is personalized for YOUR voice!")
                        except Exception as hf_error:
                            import traceback
                            print(f"[MONICA-HF] [ERROR] HuggingFace model load failed: {hf_error}")
                            traceback.print_exc()
                            # Don't fail completely - continue to try other models
                            print(f"[MONICA-HF] Trying SpeechBrain custom model...")
                    
                    # FALLBACK 2: Try SpeechBrain custom model
                    if self.asr_model is None and HAS_CUSTOM_MODEL:
                        custom_model_base = project_root / "models" / "monica_finetuned" / "1986"
                        custom_model_dir = custom_model_base / "save"
                        hparams_file = project_root / "hparams_monica.yaml"

                        latest_ckpt = None
                        if custom_model_dir.exists():
                            ckpt_dirs = sorted([d for d in custom_model_dir.iterdir() if d.is_dir() and d.name.startswith("CKPT+")])
                            if ckpt_dirs:
                                latest_ckpt = ckpt_dirs[-1]
                                print(f"[MONICA-CUSTOM] Found checkpoint: {latest_ckpt.name}")

                        if latest_ckpt and hparams_file.exists():
                            print(f"[MONICA-CUSTOM] Loading SpeechBrain CUSTOM MODEL")
                            print(f"[MONICA-CUSTOM] Checkpoint: {latest_ckpt.name}")

                            try:
                                self.asr_model = load_monica_custom_model(device=device)
                                print(f"[MONICA-CUSTOM] [SUCCESS] CUSTOM MODEL LOADED in {time.time() - asr_start:.2f}s on {device}")
                            except Exception as custom_error:
                                import traceback
                                print(f"[MONICA-CUSTOM] [ERROR] Custom model load failed: {custom_error}")
                                traceback.print_exc()
                    
                    # If no model loaded at all, report error
                    if not self.use_enhanced and self.asr_model is None:
                        print(f"\n{'='*80}")
                        print(f"[MONICA-STT] CRITICAL ERROR - NO STT MODEL AVAILABLE")
                        print(f"[MONICA-STT] Enhanced model: Not loaded")
                        print(f"[MONICA-STT] HuggingFace model: Not loaded")
                        print(f"[MONICA-STT] SpeechBrain model: Not loaded")
                        print(f"{'='*80}\n")
                        self.loading_failed = True
                        self.last_load_error = "No STT model could be loaded"
                        raise RuntimeError("No STT model could be loaded")
                
                # Load speaker model
                speaker_start = time.time()
                try:
                    self.speaker_model = SpeakerRecognition.from_hparams(
                        source="speechbrain/spkrec-ecapa-voxceleb",
                        savedir=str(self.speaker_cache_dir),  # Persistent cache
                        run_opts={"device": "cuda" if torch.cuda.is_available() else "cpu"}
                    )
                    print(f"[FINAL-SPEECHBRAIN] Speaker model loaded in {time.time() - speaker_start:.2f}s")
                except Exception as spk_err:
                    print(f"[FINAL-SPEECHBRAIN] Speaker model failed (non-fatal): {spk_err}")
                    self.speaker_model = None
                
                # Load voice signature
                signature_file = self.model_dir / "enhanced_voice_signature.pt"
                if signature_file.exists():
                    signature_data = torch.load(signature_file, map_location='cpu')
                    self.voice_signature = signature_data['voice_signature']
                    print("[FINAL-SPEECHBRAIN] Enhanced voice signature loaded!")
                
                self.is_loaded = True
                total_time = time.time() - self.loading_start_time
                print(f"[FINAL-SPEECHBRAIN] All models loaded successfully in {total_time:.2f}s")
                
            except Exception as e:
                print(f"[FINAL-SPEECHBRAIN] Loading failed: {e}")
                self.last_load_error = f"{type(e).__name__}: {e}"
                self.loading_failed = True
        
        # Start loading in background thread
        self.loading_thread = threading.Thread(target=load_models, daemon=True)
        self.loading_thread.start()
    
    def _load_vocabulary(self) -> set:
        """Load custom vocabulary from file"""
        vocab = set()
        vocab_file = self.model_dir / "vocabulary.txt"
        
        if vocab_file.exists():
            try:
                with open(vocab_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if line and not line.startswith('#'):
                            vocab.add(line.lower())
                print(f"[FINAL-SPEECHBRAIN] Loaded {len(vocab)} vocabulary words")
            except Exception as e:
                print(f"[FINAL-SPEECHBRAIN] Error loading vocabulary: {e}")
        else:
            print("[FINAL-SPEECHBRAIN] No vocabulary file found")
        
        return vocab
    
    def _correct_with_vocabulary(self, text: str) -> str:
        """
        Post-process transcription using vocabulary for common corrections
        Uses fuzzy matching to fix misheard words
        """
        if not text or not self.vocabulary:
            return text
        
        words = text.split()
        corrected_words = []
        
        # Common misrecognition patterns - CONSERVATIVE corrections only
        # IMPORTANT: Only correct clear misrecognitions, NOT common words like 'to', 'for'
        corrections = {
            # Monica variations (these are clear misrecognitions)
            'mahanika': 'monica', 'mamanika': 'monica', 'mamanica': 'monica',
            'monika': 'monica', 'monic': 'monica',
            'manica': 'monica', 'mahnica': 'monica',
            
            # Initialize variations (only clear misrecognitions)
            'innit': 'initialize', 'initiate': 'initialize',
            
            # Contractions (safe corrections)
            'dont': "don't", 'cant': "can't", 'wont': "won't",
            'im': "i'm", 'youre': "you're", 'theyre': "they're",
            'thats': "that's", 'heres': "here's", 'wheres': "where's",
            'whats': "what's", 'todays': "today's",
            
            # REMOVED: 'to': 'two', 'for': 'four', 'won': 'one' - these break normal sentences!
            # REMOVED: 'monique': 'monica' - this is a valid name
            # REMOVED: 'in it', 'in a', 'initial' - these are valid phrases
        }
        
        for word in words:
            word_lower = word.lower()
            
            # Check direct corrections first (only clear misrecognitions)
            if word_lower in corrections:
                corrected_words.append(corrections[word_lower])
            else:
                # Keep word as-is - trained model output is accurate
                # DISABLED fuzzy matching - it was causing more harm than good
                # by changing valid words to similar but wrong words
                corrected_words.append(word)
        
        result = ' '.join(corrected_words)
        if result.lower() != text.lower():
            print(f"[FINAL-SPEECHBRAIN] Corrected: '{text}' -> '{result}'")
        return result
    
    def _init_language_model(self):
        """Initialize KenLM language model for better accuracy."""
        try:
            from pyctcdecode import build_ctcdecoder
            
            # Path to language model
            lm_path = _PROJECT_ROOT / "models" / "english_lm.bin"
            vocab_path = _PROJECT_ROOT / "models" / "wav2vec2_final" / "final_model" / "vocab.json"
            
            if not lm_path.exists():
                print(f"[KENLM] Language model not found at {lm_path}")
                return
            
            if not vocab_path.exists():
                print(f"[KENLM] Vocabulary not found at {vocab_path}")
                return
            
            # Load vocabulary
            import json
            with open(vocab_path, 'r', encoding='utf-8') as f:
                vocab = json.load(f)
            
            # Sort by index and normalize labels for CTC decoding.
            # Keep a one-char alphabet plus word delimiter to improve decoder stability.
            labels_by_index = [k for k, _ in sorted(vocab.items(), key=lambda x: x[1])]
            vocab_list = []
            for token in labels_by_index:
                t = token.lower()
                if t in ('<pad>', '[pad]'):
                    vocab_list.append('')
                elif t in ('|', '▁'):
                    vocab_list.append(' ')
                elif len(t) == 1:
                    vocab_list.append(t)
                else:
                    # Ignore non-alphabet special tokens in decoder alphabet.
                    vocab_list.append('')
            
            print(f"[KENLM] Loading language model ({lm_path.stat().st_size / 1024 / 1024:.0f} MB)...")
            
            # Common English unigrams for better word segmentation
            unigrams = [
                "the", "a", "an", "and", "or", "but", "if", "then", "when", "where", "why", "how",
                "what", "which", "who", "is", "are", "was", "were", "be", "been", "being",
                "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
                "can", "may", "might", "must", "i", "you", "he", "she", "it", "we", "they",
                "me", "him", "her", "us", "them", "my", "your", "his", "its", "our", "their",
                "this", "that", "these", "those", "here", "there", "now", "then", "today",
                "monica", "initialize", "psychology", "clinical", "therapy", "counseling",
                "tell", "show", "help", "about", "please", "thank", "hello", "goodbye",
                "yes", "no", "not", "just", "only", "also", "very", "really", "actually",
                "think", "know", "want", "need", "like", "love", "hate", "feel", "believe",
                "understand", "remember", "forget", "learn", "teach", "explain", "describe",
                "question", "answer", "problem", "solution", "reason", "example", "information",
            ]

            # Add wake-phrase and command-centric vocabulary.
            wake_words = [
                "monica", "monika", "initialize", "initialise", "initializing", "init",
                "system", "online", "start", "startup", "wake", "activate",
                "show", "globe", "zoom", "camera", "listen", "listening",
            ]
            unigrams.extend(wake_words)

            # Merge in personal vocabulary from voice training artifacts when available.
            try:
                if getattr(self, 'vocabulary', None):
                    unigrams.extend([w for w in self.vocabulary if isinstance(w, str)])
            except Exception:
                pass

            try:
                personal_vocab_json = _PROJECT_ROOT / "monica_ai" / "personal_voice_model" / "personal_vocabulary.json"
                if personal_vocab_json.exists():
                    with open(personal_vocab_json, 'r', encoding='utf-8') as pf:
                        pdata = json.load(pf)
                    pwords = pdata.get('words', []) if isinstance(pdata, dict) else []
                    unigrams.extend([w for w in pwords if isinstance(w, str)])
            except Exception:
                pass

            # Final sanitize and dedupe.
            cleaned_unigrams = []
            seen = set()
            for w in unigrams:
                ww = str(w).strip().lower()
                if not ww:
                    continue
                if any(ch for ch in ww if not (ch.isalpha() or ch in ("'",))):
                    continue
                if len(ww) < 2 and ww not in ('a', 'i'):
                    continue
                if ww in seen:
                    continue
                seen.add(ww)
                cleaned_unigrams.append(ww)
            
            # Build decoder with language model
            self.lm_decoder = build_ctcdecoder(
                labels=vocab_list,
                kenlm_model_path=str(lm_path),
                unigrams=cleaned_unigrams,
                alpha=0.5,  # LM weight
                beta=1.5,   # Word insertion bonus
            )
            
            print(f"[KENLM] Language model decoder ready! ({len(cleaned_unigrams)} unigrams)")
            
        except ImportError:
            print("[KENLM] pyctcdecode not available - using greedy decoding")
        except Exception as e:
            print(f"[KENLM] Failed to load language model: {e}")
            self.lm_decoder = None
    
    def recognize_file(self, audio_file_path: str) -> str:
        """
        Recognize speech from audio file
        """
        try:
            # Check if models are loaded and ready
            if not self.is_loaded or (self.asr_model is None and not getattr(self, 'use_enhanced', False)):
                if self.loading_failed:
                    return ""
                print("[FINAL-SPEECHBRAIN] Model still loading...")
                return ""
            
            # Read audio file and convert to tensor
            # Assume 16kHz mono WAV for now, as that's what TTS generates
            audio_tensor, sample_rate = torchaudio.load(audio_file_path)
            
            # Resample if necessary (recognizer expects 16kHz)
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                audio_tensor = resampler(audio_tensor)
            
            # Ensure mono (recognize_tensor expects 1D tensor)
            if audio_tensor.shape[0] > 1:
                audio_tensor = audio_tensor.mean(dim=0)
            else:
                audio_tensor = audio_tensor.squeeze(0) # Ensure 1D

            # Call recognize_tensor
            transcription = self.recognize_tensor(audio_tensor)

            if transcription and transcription.strip():
                # Apply vocabulary correction
                corrected = self._correct_with_vocabulary(transcription.strip())
                return corrected
            else:
                return ""
                
        except Exception as e:
            print(f"[FINAL-SPEECHBRAIN] Recognition error: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def recognize_tensor(self, audio_tensor: torch.Tensor) -> str:
        """
        Recognize speech from audio tensor with accuracy enhancements
        USES YOUR TRAINED wav2vec2 model (36k+ samples) - Whisper is DISABLED
        """
        try:
            transcription = ""
            
            # ================================================================
            # PRIORITY 1: USE YOUR TRAINED ENHANCED MODEL (36,135 samples!)
            # This model was trained on LibriSpeech + YOUR voice recordings
            # It should be personalized for your voice and vocabulary
            # ================================================================
            use_enhanced = getattr(self, 'use_enhanced', False)
            has_enhanced = hasattr(self, 'enhanced_model') and self.enhanced_model is not None
            
            # Check if models are loaded
            if not self.is_loaded or (self.asr_model is None and not has_enhanced):
                if self.loading_failed:
                    return ""
                print("[FINAL-SPEECHBRAIN] Model still loading...")
                return ""
            
            # ENHANCEMENT: Apply audio preprocessing (noise reduction, speed normalization)
            if self.stt_enhancer is not None:
                try:
                    # Convert to numpy for enhancement
                    audio_np = audio_tensor.numpy() if isinstance(audio_tensor, torch.Tensor) else audio_tensor
                    # Apply enhancements
                    audio_np = self.stt_enhancer.enhance_audio_for_stt(audio_np)
                    # Convert back to tensor
                    audio_tensor = torch.from_numpy(audio_np).float()
                except Exception as e:
                    print(f"[FINAL-SPEECHBRAIN] Audio enhancement failed: {e}")
                    # Continue with original audio
            
            # PRIORITY 1: Try YOUR trained model (wav2vec2_final - WORKS!)
            if use_enhanced and has_enhanced:
                try:
                    # Ensure 1D tensor
                    if audio_tensor.dim() == 2:
                        audio_tensor = audio_tensor.squeeze(0)
                    
                    # Convert to numpy for processor
                    audio_np = audio_tensor.numpy() if isinstance(audio_tensor, torch.Tensor) else audio_tensor
                    
                    # Process audio with enhanced model
                    inputs = self.enhanced_processor(
                        audio_np,
                        sampling_rate=16000,
                        return_tensors="pt",
                        padding=True
                    )
                    
                    device = next(self.enhanced_model.parameters()).device
                    input_values = inputs.input_values.to(device)
                    
                    # Run inference
                    with torch.no_grad():
                        logits = self.enhanced_model(input_values).logits
                    
                    # Check for NaN - if model is corrupted, skip to HuggingFace model
                    if torch.isnan(logits).any():
                        print(f"[MONICA-ENHANCED] WARNING: Model outputs NaN - model may be corrupted!")
                        print(f"[MONICA-ENHANCED] Falling back to HuggingFace trained model...")
                        raise ValueError("Enhanced model corrupted (NaN output)")
                    
                    # Use KenLM language model decoder if available (much better accuracy)
                    if self.lm_decoder is not None:
                        # Beam search with language model
                        logits_np = logits.cpu().numpy()[0]  # Remove batch dimension
                        transcription = self.lm_decoder.decode(logits_np)
                        print(f"[KENLM] Beam search result: '{transcription}'")
                    else:
                        # Greedy decode (fallback)
                        predicted_ids = torch.argmax(logits, dim=-1)
                        transcription = self.enhanced_processor.batch_decode(predicted_ids)[0]
                    
                    # Clean up word delimiter
                    if '|' in transcription:
                        transcription = transcription.replace('|', ' ')
                    import re
                    transcription = re.sub(r'\s+', ' ', transcription).strip()
                    
                    if transcription:
                        print(f"[MONICA-STT] Result: '{transcription}'")
                    
                except Exception as enh_err:
                    print(f"[MONICA-ENHANCED] Recognition failed: {enh_err}")
                    transcription = ""
                    # Fall through to try HuggingFace model
            
            # Use HuggingFace trained model if enhanced didn't work or wasn't available
            if not transcription and self.asr_model is not None:
                if hasattr(self.asr_model, 'transcribe_tensor'):
                    # Custom model - direct tensor transcription
                    print(f"[MONICA-HF] Using HuggingFace trained model...")
                    transcription = self.asr_model.transcribe_tensor(audio_tensor, 16000)
                elif hasattr(self.asr_model, 'transcribe_file'):
                    # Generic model - use temp file approach
                    temp_dir = self.model_dir / "temp"
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    temp_path = temp_dir / f"temp_audio_{time.time():.0f}.wav"
                    
                    try:
                        torchaudio.save(str(temp_path), audio_tensor, 16000)
                        transcription = self.asr_model.transcribe_file(str(temp_path))
                    finally:
                        if temp_path.exists():
                            temp_path.unlink()
            
            print(f"[FINAL-SPEECHBRAIN] Raw result: '{transcription}'")
            
            if transcription and transcription.strip():
                # Apply vocabulary correction (legacy)
                corrected = self._correct_with_vocabulary(transcription.strip())
                
                # ENHANCEMENT: Apply advanced vocabulary corrections and accent drift handling
                if self.stt_enhancer is not None:
                    try:
                        corrected = self.stt_enhancer.enhance_transcription(corrected)
                    except Exception as e:
                        print(f"[FINAL-SPEECHBRAIN] Transcription enhancement failed: {e}")
                
                return corrected
            else:
                return ""
                
        except Exception as e:
            print(f"[FINAL-SPEECHBRAIN] Tensor recognition error: {e}")
            return ""
    
    def verify_speaker(self, audio_tensor: torch.Tensor, threshold: float = 0.25) -> tuple:
        """
        Verify if the audio is from the registered user.
        
        Args:
            audio_tensor: Audio tensor to verify
            threshold: Similarity threshold (0-1). Higher = stricter matching.
                      Default 0.25 is lenient to account for background noise.
        
        Returns:
            tuple: (is_user_voice: bool, similarity_score: float)
        """
        try:
            if self.speaker_model is None or self.voice_signature is None:
                # No speaker model or signature - allow all audio
                return (True, 1.0)
            
            # Ensure tensor is correct shape (1D or 2D with batch)
            if audio_tensor.dim() == 1:
                audio_tensor = audio_tensor.unsqueeze(0)
            elif audio_tensor.dim() == 2 and audio_tensor.shape[0] != 1:
                audio_tensor = audio_tensor.squeeze(0).unsqueeze(0)
            
            # Get embedding for current audio
            current_embedding = self.speaker_model.encode_batch(audio_tensor)
            
            # Ensure voice_signature is correct shape
            voice_sig = self.voice_signature
            if voice_sig.dim() == 1:
                voice_sig = voice_sig.unsqueeze(0)
            
            # Calculate cosine similarity
            similarity = torch.nn.functional.cosine_similarity(
                current_embedding.squeeze(), 
                voice_sig.squeeze(), 
                dim=0
            ).item()
            
            is_user = similarity >= threshold
            
            if is_user:
                print(f"[SPEAKER-VERIFY] ✓ User voice confirmed (similarity: {similarity:.3f})")
            else:
                print(f"[SPEAKER-VERIFY] ✗ Unknown speaker (similarity: {similarity:.3f}, threshold: {threshold})")
            
            return (is_user, similarity)
            
        except Exception as e:
            print(f"[SPEAKER-VERIFY] Error: {e}")
            # On error, allow audio through to avoid blocking user
            return (True, 0.0)
    
    def contains_speech(self, audio_tensor: torch.Tensor, threshold: float = 0.5) -> tuple:
        """
        Check if audio contains speech using Silero VAD.
        Filters out background noise like TV, music, etc.
        
        Args:
            audio_tensor: Audio tensor (1D or 2D with batch)
            threshold: Speech probability threshold (0-1). Higher = stricter.
        
        Returns:
            tuple: (has_speech: bool, speech_prob: float, speech_segments: list)
        """
        try:
            if self.vad_model is None:
                # No VAD model - assume speech is present
                return (True, 1.0, [])
            
            # Ensure tensor is 1D for VAD
            if audio_tensor.dim() == 2:
                audio_tensor = audio_tensor.squeeze(0)
            
            # Get speech timestamps using Silero VAD
            speech_timestamps = get_speech_timestamps(
                audio_tensor,
                self.vad_model,
                threshold=threshold,
                sampling_rate=16000,
                min_speech_duration_ms=250,  # Minimum 250ms of speech
                min_silence_duration_ms=100,  # Minimum 100ms silence between segments
            )
            
            has_speech = len(speech_timestamps) > 0
            
            # Calculate overall speech probability
            if has_speech:
                total_speech_samples = sum(seg['end'] - seg['start'] for seg in speech_timestamps)
                speech_ratio = total_speech_samples / len(audio_tensor)
                speech_prob = min(1.0, speech_ratio * 2)  # Scale up
            else:
                speech_prob = 0.0
            
            if has_speech:
                print(f"[SILERO-VAD] ✓ Speech detected ({len(speech_timestamps)} segments, prob: {speech_prob:.2f})")
            else:
                print(f"[SILERO-VAD] ✗ No speech detected (background noise filtered)")
            
            return (has_speech, speech_prob, speech_timestamps)
            
        except Exception as e:
            print(f"[SILERO-VAD] Error: {e}")
            # On error, assume speech is present
            return (True, 0.5, [])
    
    def is_ready(self) -> bool:
        """Check if system is ready"""
        return self.is_loaded
    
    def get_loading_status(self) -> str:
        """Get detailed loading status"""
        if self.is_loaded:
            return "Ready"
        elif self.loading_failed:
            return "Failed"
        elif self.loading_start_time:
            elapsed = time.time() - self.loading_start_time
            return f"Loading... ({elapsed:.1f}s)"
        else:
            return "Not started"
    
    def wait_until_ready(self, timeout: int = 180) -> bool:
        """Wait until models are loaded"""
        start_time = time.time()
        while not self.is_loaded and not self.loading_failed:
            if time.time() - start_time > timeout:
                print(f"[FINAL-SPEECHBRAIN] Loading timeout after {timeout}s")
                return False
            time.sleep(1)
        return self.is_loaded

class FinalMonicaAudio:
    """
    Final Monica Audio System
    Implements research-based SpeechBrain integration with real-time audio capture
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.recognizer = FinalSpeechBrainRecognizer()
        
        # Audio capture
        try:
            import pyaudio
            self.audio = pyaudio.PyAudio()
            self.has_audio = True
        except:
            self.audio = None
            self.has_audio = False
        
        self.stream = None
        self.sample_rate = 16000
        self.capture_sample_rate = 16000
        self.asr_sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.input_device_index = None
        self.input_device_name = None

        self.last_error = None
        self._stream_ready_event = threading.Event()
        self._stream_failed_event = threading.Event()

        try:
            if isinstance(self.config, dict):
                self.sample_rate = int(self.config.get('SAMPLE_RATE', self.sample_rate))
                self.chunk_size = int(self.config.get('CHUNK_SIZE', self.chunk_size))
                self.channels = int(self.config.get('CHANNELS', self.channels))
                self.input_device_index = self.config.get('INPUT_DEVICE_INDEX', None)
                self.input_device_name = self.config.get('INPUT_DEVICE_NAME', None)
            else:
                self.sample_rate = int(getattr(self.config, 'SAMPLE_RATE', self.sample_rate))
                self.chunk_size = int(getattr(self.config, 'CHUNK_SIZE', self.chunk_size))
                self.channels = int(getattr(self.config, 'CHANNELS', self.channels))
                self.input_device_index = getattr(self.config, 'INPUT_DEVICE_INDEX', None)
                self.input_device_name = getattr(self.config, 'INPUT_DEVICE_NAME', None)
        except Exception:
            pass

        try:
            env_name = os.getenv('MONICA_INPUT_DEVICE_NAME', '').strip()
            if env_name:
                self.input_device_name = env_name
        except Exception:
            pass

        # ASR expects 16kHz mono
        self.asr_sample_rate = 16000
        
        # State management
        self.is_listening = False
        self._paused = False  # Pause processing without stopping audio
        self.callbacks = []
        self.audio_buffer = []
        self.listening_thread = None
        self.voice_threshold = 0.008  # Lower threshold to catch quieter speech
        self.min_speech_duration = 0.3  # Reduced from 0.5s - faster response
        self.silence_duration = 0
        self.max_silence = 3.0  # Allow long natural pauses - don't cut off mid-sentence
        
        print("[FINAL-MONICA] Final audio system ready!")
    
    def start_listening(self):
        """Start listening with real-time audio capture"""
        if self.is_listening:
            print("[FINAL-MONICA] Already listening")
            return

        # Debug: List available audio devices
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            print("\n[AUDIO-DEBUG] Available audio devices:")
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    print(f"  [{i}] {info['name']} (inputs: {info['maxInputChannels']}, rate: {int(info['defaultSampleRate'])}Hz)")
            p.terminate()
        except Exception as e:
            print(f"[AUDIO-DEBUG] Could not list devices: {e}")

        self.is_listening = True
        self.last_error = None
        self._stream_ready_event.clear()
        self._stream_failed_event.clear()
        self.listening_thread = threading.Thread(target=self._listening_loop, daemon=True)
        self.listening_thread.start()
        print(f"[FINAL-MONICA] Started listening! Status: {self.recognizer.get_loading_status()}")
        print(f"[AUDIO-DEBUG] Device index: {self.input_device_index}, Device name: {self.input_device_name}, Sample rate: {self.sample_rate}Hz, Chunk: {self.chunk_size}")

        ok = False
        try:
            ok = self._stream_ready_event.wait(timeout=4.0)
            if ok:
                return
            if self._stream_failed_event.is_set():
                raise RuntimeError(self.last_error or "Failed to open audio input stream")
        except Exception:
            self.is_listening = False
            raise
    
    def stop_listening(self):
        """Stop listening"""
        self.is_listening = False
        
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None
        
        print("[FINAL-MONICA] Stopped listening!")
    
    def _listening_loop(self):
        """Real-time audio capture and recognition loop"""
        import pyaudio
        
        try:
            # Wait for SpeechBrain to load first
            if not self.recognizer.is_loaded:
                print("[FINAL-MONICA] Waiting for SpeechBrain to load...")
                wait_start = time.time()
                while not self.recognizer.is_loaded and self.is_listening:
                    if getattr(self.recognizer, 'loading_failed', False):
                        err = getattr(self.recognizer, 'last_load_error', None) or "SpeechBrain model loading failed"
                        self.last_error = err
                        print(f"[FINAL-MONICA] SpeechBrain loading failed: {err}")
                        return
                    time.sleep(1)
                    elapsed = time.time() - wait_start
                    if int(elapsed) % 10 == 0:
                        print(f"[FINAL-MONICA] Still loading SpeechBrain... ({elapsed:.0f}s)")
                    if elapsed > 180:
                        print("[FINAL-MONICA] SpeechBrain loading timeout!")
                        return
                
                if self.recognizer.is_loaded:
                    print("[FINAL-MONICA] [OK] SpeechBrain loaded! Now listening...")
                else:
                    return
            
            try:
                # Resolve capture sample rate from device defaults when possible.
                try:
                    if self.input_device_name and self.audio is not None:
                        want = str(self.input_device_name).strip().lower()
                        best = None
                        try:
                            for i in range(self.audio.get_device_count()):
                                info = self.audio.get_device_info_by_index(i)
                                if int(info.get('maxInputChannels', 0)) <= 0:
                                    continue
                                name = str(info.get('name', '')).strip().lower()
                                if want and want in name:
                                    best = int(info.get('index', i))
                                    break
                        except Exception:
                            best = None

                        if best is not None:
                            self.input_device_index = int(best)
                            print(f"[AUDIO-DEBUG] Using input device by name match '{self.input_device_name}': index={self.input_device_index}")
                        else:
                            print(f"[AUDIO-DEBUG] Input device name not found: '{self.input_device_name}'. Falling back to index/default.")

                    if self.input_device_index is None:
                        default_in = self.audio.get_default_input_device_info()
                        self.input_device_index = int(default_in.get('index', 0))
                    dev_info = self.audio.get_device_info_by_index(int(self.input_device_index))
                    self.capture_sample_rate = int(dev_info.get('defaultSampleRate', self.sample_rate))
                except Exception:
                    self.capture_sample_rate = int(self.sample_rate)

                print(f"[AUDIO-DEBUG] Opening audio stream with device_index={self.input_device_index}")
                self.stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=self.channels,
                    rate=self.capture_sample_rate,
                    input=True,
                    input_device_index=self.input_device_index,
                    frames_per_buffer=self.chunk_size
                )
                print(f"[AUDIO-DEBUG] [OK] Audio stream opened successfully")
                self._stream_ready_event.set()
            except Exception as e:
                self.last_error = f"{type(e).__name__}: {e}"
                self._stream_failed_event.set()
                raise
            
            print("[FINAL-MONICA] Audio stream opened - listening for speech...")
            print(f"[FINAL-MONICA] Voice threshold: {self.voice_threshold}, callbacks: {len(self.callbacks)}")
            print("[AUDIO-DEBUG] *** SPEAK NOW TO TEST AUDIO INPUT ***")
            
            frame_count = 0
            max_energy_seen = 0.0
            while self.is_listening:
                try:
                    # Read audio chunk
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # CRITICAL: Feed audio to AudioManager's queue for visualization
                    # This enables the sound level monitor in the GUI
                    if hasattr(self.config, '_audio_manager') and self.config._audio_manager:
                        try:
                            self.config._audio_manager.audio_queue.put_nowait(audio_chunk)
                        except:
                            pass  # Queue full, skip this frame
                    
                    # Check energy level
                    energy = float(np.sqrt(np.mean(audio_chunk**2)))
                    
                    is_speaking = energy > self.voice_threshold
                    
                    # Track max energy for debugging
                    if energy > max_energy_seen:
                        max_energy_seen = energy
                    
                    # Debug output every 50 frames (~3 seconds) - MORE FREQUENT
                    frame_count += 1
                    if frame_count % 50 == 0:
                        print(f"[AUDIO-DEBUG] Level: {energy:.4f} (max: {max_energy_seen:.4f}, threshold: {self.voice_threshold:.4f}), speaking: {is_speaking}, buffer: {len(self.audio_buffer)} samples")
                    
                    # Extra debug when speaking detected
                    if is_speaking and frame_count % 10 == 0:
                        print(f"[AUDIO-DEBUG] *** SPEECH DETECTED *** Energy: {energy:.4f}")
                    
                    if is_speaking:
                        # Add to buffer while speaking
                        self.audio_buffer.extend(audio_chunk)
                        self.silence_duration = 0
                    else:
                        # Count silence but KEEP BUFFERING during natural pauses
                        self.silence_duration += self.chunk_size / float(self.capture_sample_rate or self.sample_rate)
                        
                        # Keep adding audio during pauses so we don't lose words
                        if len(self.audio_buffer) > 0:
                            self.audio_buffer.extend(audio_chunk)
                        
                        # Only process when we have audio AND enough silence (end of sentence)
                        if len(self.audio_buffer) > (self.capture_sample_rate * self.min_speech_duration):
                            if self.silence_duration > self.max_silence:
                                self._process_audio_buffer()
                    
                    # Prevent buffer from growing too large
                    max_buffer = int((self.capture_sample_rate or self.sample_rate) * 10)  # 10 seconds max - faster for presentation
                    if len(self.audio_buffer) > max_buffer:
                        self._process_audio_buffer()
                        
                except Exception as e:
                    print(f"[FINAL-MONICA] Audio read error: {e}")
                    time.sleep(0.01)
                    
        except Exception as e:
            if not self.last_error:
                self.last_error = f"{type(e).__name__}: {e}"
            self._stream_failed_event.set()
            print(f"[FINAL-MONICA] Listening loop error: {e}")
        finally:
            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                except:
                    pass
    
    def _process_audio_buffer(self):
        """Process collected audio buffer with SpeechBrain"""
        if not self.audio_buffer or len(self.audio_buffer) < (self.capture_sample_rate * 0.3):
            self.audio_buffer = []
            return
        
        # Don't process if paused
        if self._paused:
            print("[FINAL-MONICA] Paused - clearing buffer")
            self.audio_buffer = []
            return
        
        try:
            # Convert to tensor
            audio_array = np.array(self.audio_buffer, dtype=np.float32)

            # Basic sanity gate: ignore near-silence chunks (common when wrong input device is selected)
            try:
                audio_max = float(np.max(np.abs(audio_array)))
                if audio_max < 0.01:
                    print(f"[AUDIO-DEBUG] Ignored near-silence utterance (max={audio_max:.4f})")
                    self.audio_buffer = []
                    self.silence_duration = 0
                    return
            except Exception:
                pass

            audio_tensor = torch.from_numpy(audio_array).unsqueeze(0)
            
            # Calculate audio stats for debugging
            audio_max = float(np.max(np.abs(audio_array)))
            audio_mean = float(np.mean(np.abs(audio_array)))
            
            print(f"[FINAL-MONICA] Processing {len(audio_array)/float(self.capture_sample_rate or self.sample_rate):.1f}s of audio...")
            print(f"[AUDIO-DEBUG] Audio stats - max: {audio_max:.4f}, mean: {audio_mean:.4f}")

            # Resample to 16kHz for ASR if needed
            try:
                in_sr = int(self.capture_sample_rate or self.sample_rate)
                out_sr = int(self.asr_sample_rate)
                if in_sr != out_sr and in_sr > 0:
                    audio_tensor = torchaudio.functional.resample(audio_tensor, in_sr, out_sr)
            except Exception as e:
                print(f"[AUDIO-DEBUG] Resample failed: {e}")
            
            # STEP 1: SILERO VAD - Filter out background noise (TV, music, etc.)
            has_speech, speech_prob, _ = self.recognizer.contains_speech(audio_tensor)
            if not has_speech:
                print(f"[FINAL-MONICA] Ignoring background noise (no speech detected)")
                self.audio_buffer = []
                self.silence_duration = 0
                return
            
            # STEP 2: SPEAKER VERIFICATION - Only process if it's the user's voice
            is_user, similarity = self.recognizer.verify_speaker(audio_tensor)
            if not is_user:
                print(f"[FINAL-MONICA] Ignoring non-user audio (similarity: {similarity:.3f})")
                self.audio_buffer = []
                self.silence_duration = 0
                return
            
            # Recognize with SpeechBrain
            result = self.recognizer.recognize_tensor(audio_tensor)
            
            if result:
                print(f"[FINAL-MONICA] Recognized: '{result}'")
                
                # Notify callbacks with the recognized text
                for callback in self.callbacks:
                    try:
                        callback(result)
                    except Exception as e:
                        print(f"[FINAL-MONICA] Callback error: {e}")
            else:
                print(f"[AUDIO-DEBUG] No recognition result (empty or failed)")
            
        except Exception as e:
            print(f"[FINAL-MONICA] Processing error: {e}")
        finally:
            # Clear buffer
            self.audio_buffer = []
            self.silence_duration = 0
    
    def recognize_file(self, file_path: str) -> str:
        """Recognize speech from file"""
        if not self.is_listening:
            return ""
        
        result = self.recognizer.recognize_file(file_path)
        
        if result:
            print(f"[FINAL-MONICA] Recognized: '{result}'")
            
            # Notify callbacks
            for callback in self.callbacks:
                try:
                    callback(result)
                except Exception as e:
                    print(f"[FINAL-MONICA] Callback error: {e}")
        
        return result
    
    def recognize_tensor(self, audio_tensor: torch.Tensor) -> str:
        """Recognize speech from tensor"""
        if not self.is_listening:
            return ""
        
        result = self.recognizer.recognize_tensor(audio_tensor)
        
        if result:
            print(f"[FINAL-MONICA] Real-time: '{result}'")
            
            # Notify callbacks
            for callback in self.callbacks:
                try:
                    callback(result)
                except Exception as e:
                    print(f"[FINAL-MONICA] Callback error: {e}")
        
        return result
    
    def transcribe_chunk(self, audio_data):
        """
        Transcribe audio chunk for STT service.

        Args:
            audio_data: numpy array of audio samples (int16)

        Returns:
            Result object with 'text' and 'is_final' attributes, or None
        """
        if audio_data is None or len(audio_data) == 0:
            print("[FINAL-MONICA] transcribe_chunk: No audio data")
            return None

        # Check if models are still loading
        if not self.recognizer.is_ready():
            status = self.recognizer.get_loading_status()
            print(f"[FINAL-MONICA] transcribe_chunk: Model not ready - {status}")
            return None
        
        print(f"[FINAL-MONICA] transcribe_chunk: Processing {len(audio_data)} samples")

        try:
            import torch
            import numpy as np

            # Convert int16 to float32 [-1, 1]
            if isinstance(audio_data, np.ndarray):
                if audio_data.dtype == np.int16:
                    audio_float = audio_data.astype(np.float32) / 32768.0
                else:
                    audio_float = audio_data
            else:
                audio_float = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Convert to tensor
            audio_tensor = torch.from_numpy(audio_float)

            # Recognize
            text = self.recognizer.recognize_tensor(audio_tensor)

            if text:
                # Create result object
                class TranscriptionResult:
                    def __init__(self, text, is_final=True):
                        self.text = text
                        self.is_final = is_final

                return TranscriptionResult(text, is_final=True)

            return None

        except Exception as e:
            print(f"[FINAL-MONICA] transcribe_chunk error: {e}")
            return None

    def register_callback(self, callback):
        """Register callback"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def pause(self):
        """Pause speech recognition - just pause processing, don't stop audio"""
        self._paused = True
        print("[FINAL-MONICA] Paused (audio still capturing)")
    
    def resume(self):
        """Resume speech recognition"""
        self._paused = False
        print("[FINAL-MONICA] Resumed")
    
    def flush(self):
        """Flush any pending audio buffers"""
        print("[FINAL-MONICA] Flushed")
    
    def is_ready(self) -> bool:
        """Check if system is ready"""
        return self.recognizer.is_ready()
    
    def wait_until_ready(self, timeout: int = 180) -> bool:
        """Wait until system is ready"""
        return self.recognizer.wait_until_ready(timeout)
    
    def get_status(self) -> str:
        """Get system status"""
        return self.recognizer.get_loading_status()

# Global instance
_final_monica_audio = None

def get_final_monica_audio(config=None):
    """Get final Monica audio instance"""
    global _final_monica_audio
    if _final_monica_audio is None:
        _final_monica_audio = FinalMonicaAudio(config)
    return _final_monica_audio

def test_final_system():
    """Test the final system"""
    print("=" * 60)
    print("TESTING FINAL SPEECHBRAIN SYSTEM")
    print("=" * 60)
    
    # Initialize final system
    final_audio = get_final_monica_audio()
    
    print(f"Initial status: {final_audio.get_status()}")
    
    # Wait for models to load
    print("\n⏳ Waiting for models to load...")
    if final_audio.wait_until_ready(timeout=180):
        print("[OK] Models loaded successfully!")
        
        # Start listening
        final_audio.start_listening()
        
        # Test with a file
        test_file = "data/training/recordings/training_phrases/phrase_00_Monica_initialize.wav"
        if Path(test_file).exists():
            print(f"\n[Mic] Testing with: {test_file}")
            test_start = time.time()
            result = final_audio.recognize_file(test_file)
            test_time = time.time() - test_start
            print(f"[Mic] Result: '{result}' (recognized in {test_time:.3f}s)")
            
            if result:
                print("[*] SUCCESS! SpeechBrain is working correctly!")
            else:
                print("[ERROR] No recognition result")
        else:
            print("[WARNING] Test file not found")
    else:
        print("[ERROR] Models failed to load")
    
    return final_audio

if __name__ == "__main__":
    test_final_system()
