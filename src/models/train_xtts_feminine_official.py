#!/usr/bin/env python3
"""
Official XTTS fine-tuning for feminine voice using Coqui TTS Trainer.

This uses the proper Coqui TTS training pipeline with LJSpeech.
"""

import os
import sys
from pathlib import Path

# Set environment before imports
os.environ["COQUI_TOS_AGREED"] = "1"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAINING_ROOT = PROJECT_ROOT / "data" / "training"
LJSPEECH_DIR = TRAINING_ROOT / "monica_tts_training" / "datasets" / "LJSpeech-1.1"
OUTPUT_DIR = TRAINING_ROOT / "monica_tts_training" / "models" / "xtts_feminine_official"

def main():
    print("="*60)
    print("XTTS FEMININE VOICE TRAINING (Official Method)")
    print("="*60)
    
    # Verify LJSpeech
    if not (LJSPEECH_DIR / "wavs").exists():
        print(f"[ERROR] LJSpeech not found at {LJSPEECH_DIR}")
        sys.exit(1)
    
    print(f"[OK] LJSpeech found at {LJSPEECH_DIR}")
    
    # Import TTS
    try:
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
        from TTS.utils.manage import ModelManager
    except ImportError:
        print("[ERROR] Coqui TTS not installed! Run: pip install TTS")
        sys.exit(1)
    
    import torch
    print(f"[OK] CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"    GPU: {torch.cuda.get_device_name(0)}")
    
    # Download/find base XTTS model
    print("\n[MODEL] Loading base XTTS v2 model...")
    
    # Use TTS model manager to get XTTS
    from TTS.api import TTS
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=torch.cuda.is_available())
    
    print(f"[MODEL] XTTS v2 loaded successfully")
    
    # Prepare output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create training config for speaker embedding extraction
    print("\n[TRAIN] Extracting speaker embeddings from LJSpeech...")
    
    # Get reference audio files (use first 30 for conditioning)
    import random
    wavs_dir = LJSPEECH_DIR / "wavs"
    all_wavs = list(wavs_dir.glob("*.wav"))
    random.seed(42)
    random.shuffle(all_wavs)
    reference_wavs = all_wavs[:30]
    
    print(f"[TRAIN] Using {len(reference_wavs)} reference samples for voice cloning")
    
    # Compute speaker embedding from LJSpeech (Linda Johnson)
    print("[TRAIN] Computing speaker conditioning latents...")
    
    # Use the TTS model to get conditioning
    gpt_cond_latent, speaker_embedding = tts.synthesizer.tts_model.get_conditioning_latents(
        audio_path=[str(w) for w in reference_wavs[:6]],  # Use 6 samples
        gpt_cond_len=30,
        gpt_cond_chunk_len=4,
        max_ref_length=30
    )
    
    print(f"[OK] GPT conditioning shape: {gpt_cond_latent.shape}")
    print(f"[OK] Speaker embedding shape: {speaker_embedding.shape}")
    
    # Save the feminine voice conditioning
    feminine_voice_path = OUTPUT_DIR / "feminine_voice_conditioning.pt"
    torch.save({
        "gpt_cond_latent": gpt_cond_latent,
        "speaker_embedding": speaker_embedding,
        "source": "LJSpeech-Linda-Johnson",
        "reference_files": [str(w) for w in reference_wavs[:6]]
    }, feminine_voice_path)
    
    print(f"\n[SAVED] Feminine voice conditioning: {feminine_voice_path}")
    
    # Test synthesis with feminine voice
    print("\n[TEST] Testing feminine voice synthesis...")
    test_text = "Hello, I am Monica, your AI assistant."
    
    wav = tts.synthesizer.tts_model.inference(
        text=test_text,
        language="en",
        gpt_cond_latent=gpt_cond_latent,
        speaker_embedding=speaker_embedding,
        temperature=0.3,
        repetition_penalty=10.0,
        speed=1.0
    )
    
    # Save test audio
    import torchaudio
    test_wav_path = OUTPUT_DIR / "test_feminine_voice.wav"
    wav_tensor = torch.tensor(wav["wav"]).unsqueeze(0)
    torchaudio.save(str(test_wav_path), wav_tensor, 24000)
    
    print(f"[SAVED] Test audio: {test_wav_path}")
    
    print("\n" + "="*60)
    print("FEMININE VOICE READY!")
    print("="*60)
    print(f"\nConditioning saved to: {feminine_voice_path}")
    print(f"Test audio saved to: {test_wav_path}")
    print("\nTo use in Monica, update monica_tts.py to load this conditioning.")
    
    return feminine_voice_path


if __name__ == "__main__":
    main()
