#!/usr/bin/env python3
"""
Quick setup for feminine voice using LJSpeech reference audio.
This extracts speaker conditioning from LJSpeech and saves it for Monica.
"""
import os
os.environ['COQUI_TOS_AGREED'] = '1'

import torch
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
LJSPEECH_DIR = PROJECT_ROOT / "monica_tts_training" / "datasets" / "LJSpeech-1.1" / "wavs"
OUTPUT_FILE = PROJECT_ROOT / "monica_tts_training" / "models" / "feminine_speaker.pt"

def main():
    print("=" * 50)
    print("Setting up feminine voice for Monica")
    print("=" * 50)
    
    # Check LJSpeech
    if not LJSPEECH_DIR.exists():
        print(f"ERROR: LJSpeech not found at {LJSPEECH_DIR}")
        return False
    
    wavs = list(LJSPEECH_DIR.glob("*.wav"))[:10]
    if len(wavs) < 3:
        print("ERROR: Need at least 3 wav files")
        return False
    
    print(f"Found {len(wavs)} reference wavs")
    
    # Load XTTS
    print("Loading XTTS model...")
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts
    
    # Use existing trained model
    xtts_dir = PROJECT_ROOT / "monica_tts_training" / "models" / "xtts_official_trained" / "run" / "training" / "XTTS_v2.0_original_model_files"
    checkpoint = PROJECT_ROOT / "monica_tts_training" / "models" / "xtts_official_trained" / "run" / "accent_tune" / "training_20251221_060349" / "GPT_XTTS_Monica_AccentTune-December-21-2025_06+04AM-e561190" / "best_model.pth"
    
    config = XttsConfig()
    config.load_json(str(xtts_dir / "config.json"))
    
    model = Xtts.init_from_config(config)
    model.load_checkpoint(
        config,
        checkpoint_dir=str(checkpoint.parent),
        checkpoint_path=str(checkpoint),
        vocab_path=str(xtts_dir / "vocab.json"),
        use_deepspeed=False
    )
    model.cuda()
    
    # Extract conditioning from LJSpeech
    print("Extracting feminine voice conditioning...")
    ref_wavs = [str(w) for w in wavs[:6]]
    
    gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(
        audio_path=ref_wavs,
        gpt_cond_len=30,
        gpt_cond_chunk_len=4,
        max_ref_length=30
    )
    
    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "gpt_cond_latent": gpt_cond_latent.cpu(),
        "speaker_embedding": speaker_embedding.cpu(),
        "source": "LJSpeech-Linda-Johnson"
    }, OUTPUT_FILE)
    
    print(f"Saved feminine voice to: {OUTPUT_FILE}")
    
    # Test
    print("Testing synthesis...")
    wav = model.inference(
        text="Hello, I am Monica, your AI assistant.",
        language="en",
        gpt_cond_latent=gpt_cond_latent,
        speaker_embedding=speaker_embedding,
        temperature=0.3,
        speed=1.0
    )
    
    import torchaudio
    test_file = OUTPUT_FILE.parent / "test_feminine.wav"
    torchaudio.save(str(test_file), torch.tensor(wav["wav"]).unsqueeze(0), 24000)
    print(f"Test audio: {test_file}")
    
    print("\n" + "=" * 50)
    print("SUCCESS! Feminine voice ready.")
    print("=" * 50)
    return True

if __name__ == "__main__":
    main()
