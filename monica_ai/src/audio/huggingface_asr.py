"""
HuggingFace ASR Loader for Monica's Custom Trained Model
Loads the wav2vec2 model trained on YOUR 1,113 voice recordings
Enhanced with KenLM language model and LLM post-processing
"""

import torch
import numpy as np
from pathlib import Path
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

# Import language model enhancements
try:
    from .stt_language_model import get_language_model_decoder, HAS_KENLM, HAS_PYCTCDECODE
    HAS_LM_DECODER = True
except ImportError:
    HAS_LM_DECODER = False
    HAS_KENLM = False
    HAS_PYCTCDECODE = False

# LLM post-processor is disabled in STT process to keep it lightweight and stable
# (Large grammar models can spike memory and stall/crash the STT process. If needed,
# this can be enabled from the AI service instead.)
HAS_LLM_POSTPROCESSOR = False

class HuggingFaceASR:
    """
    ASR using HuggingFace Transformers wav2vec2 model
    Trained on your personal voice recordings
    """
    
    def __init__(self, model_path: str = None, device: str = None):
        """
        Initialize the HuggingFace ASR model
        
        Args:
            model_path: Path to the trained model directory
            device: Device to run on ('cuda' or 'cpu')
        """
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        # Default model path - use the newly trained model (WER 14.59%)
        if model_path is None:
            project_root = Path(__file__).resolve().parents[3]
            model_path = project_root / "models" / "wav2vec2_final" / "final_model"
        
        self.model_path = Path(model_path)
        
        print(f"[HUGGINGFACE-ASR] Loading model from: {self.model_path}")
        print(f"[HUGGINGFACE-ASR] Device: {self.device}")
        
        # Language model decoder (optional)
        self.lm_decoder = None
        self.use_lm = False
        
        # LLM post-processor (optional)
        self.llm_postprocessor = None
        self.use_llm_cleanup = False
        
        # Load processor and model
        try:
            self.processor = Wav2Vec2Processor.from_pretrained(str(self.model_path))
            self.model = Wav2Vec2ForCTC.from_pretrained(str(self.model_path))
            self.model.to(self.device)
            self.model.eval()
            
            print(f"[HUGGINGFACE-ASR] Model loaded successfully!")
            print(f"[HUGGINGFACE-ASR] Device: {self.device}")
            print(f"[HUGGINGFACE-ASR] Model device: {next(self.model.parameters()).device}")
            print(f"[HUGGINGFACE-ASR] This model was trained on YOUR voice recordings!")
            
            # GPU verification
            if torch.cuda.is_available():
                if self.device == "cuda" or "cuda" in str(next(self.model.parameters()).device):
                    print(f"[HUGGINGFACE-ASR] [OK] Using GPU acceleration")
                else:
                    print(f"[HUGGINGFACE-ASR] [WARNING] CUDA available but model on CPU - may be slower")
            
            self.is_loaded = True
            
            # Initialize beam search decoder (works with or without KenLM)
            if HAS_LM_DECODER and HAS_PYCTCDECODE:
                try:
                    vocab_file = self.model_path / "vocab.json"
                    if vocab_file.exists():
                        self.lm_decoder = get_language_model_decoder(vocab_file)
                        if self.lm_decoder.is_available():
                            self.use_lm = True
                            print("[HUGGINGFACE-ASR] [OK] Beam search decoder enabled")
                        else:
                            print("[HUGGINGFACE-ASR] [WARNING] Beam search not available")
                except Exception as e:
                    print(f"[HUGGINGFACE-ASR] Beam search init failed: {e}")
            
            # LLM post-processor intentionally disabled here
            if HAS_LLM_POSTPROCESSOR:
                pass
            
        except Exception as e:
            print(f"[HUGGINGFACE-ASR] Failed to load model: {e}")
            self.is_loaded = False
            raise
    
    def transcribe_tensor(self, audio_tensor: torch.Tensor, sample_rate: int = 16000) -> str:
        """
        Transcribe audio from a tensor
        
        Args:
            audio_tensor: Audio tensor [samples] or [1, samples]
            sample_rate: Sample rate (should be 16000)
            
        Returns:
            Transcribed text
        """
        if not self.is_loaded:
            return ""
        
        try:
            # Ensure 1D tensor
            if audio_tensor.dim() == 2:
                audio_tensor = audio_tensor.squeeze(0)
            
            # Convert to numpy for processor
            audio_np = audio_tensor.numpy() if isinstance(audio_tensor, torch.Tensor) else audio_tensor
            
            # Process audio
            inputs = self.processor(
                audio_np,
                sampling_rate=sample_rate,
                return_tensors="pt",
                padding=True
            )
            
            input_values = inputs.input_values.to(self.device)
            
            # Run inference
            with torch.no_grad():
                logits = self.model(input_values).logits
            
            # CRITICAL FIX: KenLM was returning empty results
            # Use greedy decoding FIRST, then optionally enhance with LM
            # This ensures we ALWAYS get a result
            predicted_ids = torch.argmax(logits, dim=-1)
            transcription = self.processor.batch_decode(predicted_ids)[0]
            
            # FIX: Ensure word delimiter '|' is converted to space
            # The processor should do this but sometimes fails
            if '|' in transcription:
                transcription = transcription.replace('|', ' ')
            # Clean up multiple spaces
            import re
            transcription = re.sub(r'\s+', ' ', transcription).strip()
            
            print(f"[HUGGINGFACE-ASR] Greedy decode result: '{transcription}'")
            
            # Try KenLM enhancement if available and greedy gave a result
            if self.use_lm and self.lm_decoder and transcription and len(transcription.strip()) > 0:
                try:
                    # Use KenLM beam search for better accuracy
                    logits_np = logits.squeeze(0).cpu().numpy()
                    lm_transcription = self.lm_decoder.decode_with_lm(logits_np)
                    if lm_transcription and len(lm_transcription.strip()) > 0:
                        print(f"[HUGGINGFACE-ASR] KenLM enhanced: '{transcription}' → '{lm_transcription}'")
                        transcription = lm_transcription
                    else:
                        print(f"[HUGGINGFACE-ASR] KenLM returned empty, using greedy: '{transcription}'")
                except Exception as e:
                    print(f"[HUGGINGFACE-ASR] KenLM failed: {e}, using greedy: '{transcription}'")
            
            # DISABLED: LLM cleanup causing duplicate transcriptions
            # User reported: "Monica show yourself lonia show yourself" - text being repeated
            # Skipping LLM post-processing to fix duplicates
            # if self.use_llm_cleanup and self.llm_postprocessor:
            #     try:
            #         cleaned = self.llm_postprocessor.cleanup_transcription(transcription)
            #         if cleaned and len(cleaned) > 0:
            #             print(f"[HUGGINGFACE-ASR] LLM cleanup: '{transcription}' → '{cleaned}'")
            #             transcription = cleaned
            #     except Exception as e:
            #         print(f"[HUGGINGFACE-ASR] LLM cleanup failed: {e}")
            
            # Apply basic cleanup (capitalization, punctuation) without LLM
            transcription = self._basic_cleanup(transcription.lower().strip())
            
            return transcription
            
        except Exception as e:
            print(f"[HUGGINGFACE-ASR] Transcription error: {e}")
            return ""
    
    def _basic_cleanup(self, text: str) -> str:
        """
        Simple cleanup without LLM to avoid duplicates.
        Adds capitalization and punctuation for professional appearance.
        """
        if not text or len(text) == 0:
            return text
        
        import re
        
        # Capitalize first letter
        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
        
        # Capitalize Monica (case-insensitive replace)
        text = re.sub(r'\bmonica\b', 'Monica', text, flags=re.IGNORECASE)
        
        # Capitalize I
        text = re.sub(r'\bi\b', 'I', text)
        
        # Capitalize I'm, I'll, I've, etc.
        text = re.sub(r"\bi'm\b", "I'm", text)
        text = re.sub(r"\bi'll\b", "I'll", text)
        text = re.sub(r"\bi've\b", "I've", text)
        text = re.sub(r"\bi'd\b", "I'd", text)
        
        # Add period at end if missing punctuation
        if text and text[-1] not in '.!?':
            text += '.'
        
        # Capitalize after sentence endings
        text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        
        return text
    
    def transcribe_numpy(self, audio_array: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribe audio from a numpy array
        
        Args:
            audio_array: Audio numpy array
            sample_rate: Sample rate (should be 16000)
            
        Returns:
            Transcribed text
        """
        audio_tensor = torch.from_numpy(audio_array).float()
        return self.transcribe_tensor(audio_tensor, sample_rate)
    
    def transcribe_file(self, file_path: str) -> str:
        """
        Transcribe audio from a file
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        import torchaudio
        
        waveform, sample_rate = torchaudio.load(file_path)
        
        # Resample if needed
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            waveform = resampler(waveform)
        
        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        
        return self.transcribe_tensor(waveform.squeeze(0), 16000)


def load_huggingface_asr(device: str = None) -> HuggingFaceASR:
    """
    Load the HuggingFace ASR model
    
    Returns:
        HuggingFaceASR instance
    """
    return HuggingFaceASR(device=device)
