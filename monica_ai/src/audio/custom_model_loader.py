"""
Custom Model Loader for Monica's Trained Voice Model
Loads the wav2vec2 CTC model trained on your 1,113 recordings
"""

import torch
import torchaudio
from pathlib import Path
import numpy as np

import speechbrain as sb
from speechbrain.inference.ASR import EncoderASR
import sentencepiece as spm


class MonicaCustomASR:
    """
    Custom ASR loader for Monica's trained model
    Matches the training structure from train_monica.py
    """

    def __init__(self, model_path: Path, hparams_file: Path, device="cuda"):
        """
        Load Monica's custom trained model

        Args:
            model_path: Path to model checkpoint directory (models/monica_finetuned/1986/save/)
            hparams_file: Path to hparams file (hparams_monica.yaml)
            device: Device to load model on
        """
        self.device = device if torch.cuda.is_available() else "cpu"
        self.model_path = Path(model_path)
        self.hparams_file = Path(hparams_file)

        # Find latest checkpoint
        ckpt_dirs = sorted([d for d in self.model_path.iterdir()
                           if d.is_dir() and d.name.startswith("CKPT+")])
        if not ckpt_dirs:
            raise ValueError(f"No checkpoints found in {self.model_path}")

        self.checkpoint_dir = ckpt_dirs[-1]
        print(f"[MONICA-CUSTOM-LOADER] Loading checkpoint: {self.checkpoint_dir.name}")

        # Load SentencePiece tokenizer FIRST (before hparams to avoid initialization issues)
        tokenizer_path = self.model_path / "tokenizer.model"
        if not tokenizer_path.exists():
            # Try alternate location - go up to monica_project root (parents[3] from save folder)
            # model_path = models/monica_finetuned/1986/save
            # parents[0] = 1986, parents[1] = monica_finetuned, parents[2] = models, parents[3] = monica_project
            project_root = self.model_path.parents[3]
            tokenizer_path = project_root / "models" / "monica_tokenizer" / "monica_1000.model"
            print(f"[MONICA-CUSTOM-LOADER] Looking for tokenizer at: {tokenizer_path}")
        
        if not tokenizer_path.exists():
            raise ValueError(f"SentencePiece tokenizer not found at {tokenizer_path}")
        
        self.tokenizer = spm.SentencePieceProcessor()
        self.tokenizer.load(str(tokenizer_path))
        print(f"[MONICA-CUSTOM-LOADER] Loaded SentencePiece tokenizer with {self.tokenizer.vocab_size()} tokens")

        # Load hyperparameters - skip tokenizer initialization since we loaded it above
        from hyperpyyaml import load_hyperpyyaml
        import yaml
        
        # Read and modify YAML to skip tokenizer initialization completely
        with open(self.hparams_file, 'r') as f:
            yaml_content = f.read()
        
        # Remove ALL tokenizer-related sections from YAML
        yaml_lines = yaml_content.split('\n')
        filtered_lines = []
        skip_section = False
        
        for line in yaml_lines:
            stripped = line.strip()
            
            # Skip tokenizer definition
            if stripped.startswith('tokenizer:'):
                skip_section = True
                continue
            
            # Skip any line that references tokenizer
            if 'tokenizer' in stripped.lower() and ('!ref' in stripped or 'annotation' in stripped):
                continue
                
            # End of indented section
            if skip_section and line and not line[0].isspace():
                skip_section = False
            
            if not skip_section:
                filtered_lines.append(line)
        
        modified_yaml = '\n'.join(filtered_lines)
        
        # Load hparams with modified YAML
        # Don't override tokenizer since we removed it from YAML and loaded it separately
        overrides = {
            "save_folder": str(self.model_path),
            "output_folder": str(self.model_path.parent),
        }
        # Set overrides_must_match=False to allow loading without all keys matching
        self.hparams = load_hyperpyyaml(modified_yaml, overrides, overrides_must_match=False)

        # Load model modules
        self.modules = self.hparams["modules"]
        
        # Convert modules dict to ModuleList if needed
        if isinstance(self.modules, dict):
            import torch.nn as nn
            module_list = nn.ModuleDict()
            for name, module in self.modules.items():
                module_list[name] = module
            self.modules = module_list
        
        self.modules.to(self.device)

        # Load checkpointer
        self.checkpointer = self.hparams["checkpointer"]

        # Recover from checkpoint - this loads the trained weights!
        print(f"[MONICA-CUSTOM-LOADER] Recovering checkpoint from {self.checkpoint_dir}...")
        recovered = self.checkpointer.recover_if_possible()
        if recovered:
            print(f"[MONICA-CUSTOM-LOADER] [OK] Checkpoint recovered successfully!")
        else:
            print(f"[MONICA-CUSTOM-LOADER] [WARNING] Checkpointer didn't recover - trying manual load...")
            # Manually load the checkpoint files
            try:
                import glob
                
                # Load model checkpoint (enc + ctc_lin)
                model_ckpt_path = self.checkpoint_dir / "model.ckpt"
                if model_ckpt_path.exists():
                    model_state = torch.load(str(model_ckpt_path), map_location=self.device, weights_only=False)
                    # The model is a ModuleList containing [enc, ctc_lin]
                    if "model" in self.hparams:
                        self.hparams["model"].load_state_dict(model_state)
                        print(f"[MONICA-CUSTOM-LOADER] [OK] Manually loaded model.ckpt")
                
                # Load wav2vec2 checkpoint
                wav2vec2_ckpt_path = self.checkpoint_dir / "wav2vec2.ckpt"
                if wav2vec2_ckpt_path.exists():
                    wav2vec2_state = torch.load(str(wav2vec2_ckpt_path), map_location=self.device, weights_only=False)
                    if "wav2vec2" in self.modules:
                        self.modules["wav2vec2"].load_state_dict(wav2vec2_state)
                        print(f"[MONICA-CUSTOM-LOADER] [OK] Manually loaded wav2vec2.ckpt")
                        
            except Exception as e:
                print(f"[MONICA-CUSTOM-LOADER] Manual checkpoint load error: {e}")
                import traceback
                traceback.print_exc()

        # Set model to eval mode for inference
        self.modules.eval()
        if "model" in self.hparams:
            self.hparams["model"].eval()
        
        print(f"[MONICA-CUSTOM-LOADER] Model loaded successfully on {self.device}")
        print(f"[MONICA-CUSTOM-LOADER] This model was trained on YOUR 1,113 voice recordings!")

    def transcribe_file(self, audio_path: str) -> str:
        """Transcribe an audio file"""
        # Load audio
        sig, sr = torchaudio.load(audio_path)

        # Resample if needed
        if sr != 16000:
            resampler = torchaudio.transforms.Resample(sr, 16000)
            sig = resampler(sig)

        return self.transcribe_batch(sig.unsqueeze(0), torch.tensor([1.0]))[0]

    def transcribe_batch(self, wavs, wav_lens):
        """
        Transcribe a batch of audio

        Args:
            wavs: Audio waveforms [batch, time]
            wav_lens: Relative lengths [batch]

        Returns:
            List of transcriptions
        """
        wavs = wavs.to(self.device)
        wav_lens = wav_lens.to(self.device)

        with torch.no_grad():
            # Forward pass through wav2vec2
            if "wav2vec2" in self.modules:
                feats = self.modules["wav2vec2"](wavs, wav_lens)
            else:
                raise ValueError("Model doesn't have wav2vec2 module")

            # Forward through encoder
            if "enc" in self.modules:
                x = self.modules["enc"](feats)
            else:
                raise ValueError("Model doesn't have encoder module")

            # CTC linear layer
            if "ctc_lin" in self.modules:
                logits = self.modules["ctc_lin"](x)
            else:
                raise ValueError("Model doesn't have CTC linear layer")

            # Log softmax
            p_ctc = self.hparams["log_softmax"](logits)

            # Greedy CTC decode - this already removes blanks and duplicates
            predictions = sb.decoders.ctc_greedy_decode(
                p_ctc, wav_lens, blank_id=self.hparams["blank_index"]
            )

            # Convert tokens to text using SentencePiece
            transcriptions = []
            for pred in predictions:
                # pred is already a list of token indices after CTC decoding
                if len(pred) == 0:
                    transcriptions.append("")
                    continue
                
                # Decode indices to text
                try:
                    # Convert tensor to list if needed
                    if isinstance(pred, torch.Tensor):
                        pred = pred.cpu().tolist()
                    
                    # Filter out blank tokens
                    filtered_pred = [idx for idx in pred if idx != self.hparams["blank_index"]]
                    
                    # Decode using SentencePiece
                    text = self.tokenizer.decode(filtered_pred)
                    print(f"[MONICA-CUSTOM-LOADER] Decoded: {filtered_pred[:20]}{'...' if len(filtered_pred) > 20 else ''} -> '{text}'")
                    transcriptions.append(text)
                except Exception as e:
                    print(f"[MONICA-CUSTOM-LOADER] Decode error: {e}")
                    import traceback
                    traceback.print_exc()
                    transcriptions.append("")

            return transcriptions

    def transcribe_tensor(self, audio_tensor: torch.Tensor, sample_rate: int = 16000) -> str:
        """
        Transcribe from a torch tensor

        Args:
            audio_tensor: Audio tensor [channels, samples] or [samples]
            sample_rate: Sample rate of audio

        Returns:
            Transcription text
        """
        # Normalize to 1D mono waveform [time]
        if audio_tensor.dim() == 2 and audio_tensor.size(0) == 1:
            audio_tensor = audio_tensor.squeeze(0)
        elif audio_tensor.dim() > 2:
            audio_tensor = audio_tensor.flatten()

        # Resample if needed (operate on 1D tensor)
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            audio_tensor = resampler(audio_tensor.unsqueeze(0)).squeeze(0)

        # Final shape must be [batch, time]
        wavs = audio_tensor.unsqueeze(0)
        wav_lens = torch.tensor([1.0])

        return self.transcribe_batch(wavs, wav_lens)[0]


def load_monica_custom_model(device="cuda"):
    """
    Load Monica's custom trained model

    Returns:
        MonicaCustomASR instance
    """
    # Get project root
    project_root = Path(__file__).resolve().parents[3]

    # Model paths
    model_path = project_root / "models" / "monica_finetuned" / "1986" / "save"
    hparams_file = project_root / "hparams_monica.yaml"

    if not model_path.exists():
        raise ValueError(f"Model not found at {model_path}")
    if not hparams_file.exists():
        raise ValueError(f"Hparams file not found at {hparams_file}")

    return MonicaCustomASR(model_path, hparams_file, device=device)
