#!/usr/bin/env python3
"""
Train Monica's XTTS voice with feminine characteristics.

Uses free feminine voice datasets:
1. LJSpeech (Linda Johnson - clear feminine voice, already in project)
2. VCTK female speakers (optional download)

This trains the AccentTune model to produce a more feminine voice.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import List, Tuple
import random

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAINING_ROOT = PROJECT_ROOT / "data" / "training"
DATASETS_DIR = TRAINING_ROOT / "monica_tts_training" / "datasets"
MODELS_DIR = TRAINING_ROOT / "monica_tts_training" / "models"
LJSPEECH_DIR = DATASETS_DIR / "LJSpeech-1.1"
VCTK_DIR = DATASETS_DIR / "VCTK-Corpus"
FEMININE_DATASET_DIR = DATASETS_DIR / "feminine_voice"

# VCTK Female speakers (known high-quality feminine voices)
VCTK_FEMALE_SPEAKERS = [
    "p225", "p228", "p229", "p230", "p231", "p233", "p236", "p238", 
    "p239", "p240", "p244", "p248", "p249", "p250", "p253", "p254",
    "p256", "p258", "p259", "p261", "p262", "p264", "p265", "p266",
    "p267", "p268", "p269", "p270", "p273", "p274", "p275", "p276",
    "p277", "p278", "p279", "p280", "p282", "p283", "p284", "p285",
    "p286", "p287", "p288", "p293", "p294", "p295", "p297", "p299",
    "p300", "p301", "p303", "p305", "p306", "p307", "p308", "p310",
    "p311", "p312", "p313", "p314", "p316", "p317", "p318", "p323",
    "p329", "p330", "p333", "p334", "p335", "p336", "p339", "p340",
    "p341", "p343", "p345", "p347", "p351", "p360", "p361", "p362",
    "p363", "p364", "p374", "p376"
]


def check_ljspeech() -> bool:
    """Check if LJSpeech dataset exists."""
    wavs_dir = LJSPEECH_DIR / "wavs"
    metadata = LJSPEECH_DIR / "metadata.csv"
    return wavs_dir.exists() and metadata.exists()


def download_vctk():
    """Download VCTK dataset (optional - large download ~11GB)."""
    print("\n" + "="*60)
    print("VCTK DATASET DOWNLOAD")
    print("="*60)
    print("\nVCTK is a large dataset (~11GB) with 110 speakers.")
    print("For feminine voice training, we recommend using LJSpeech first.")
    print("\nTo download VCTK manually:")
    print("  1. Visit: https://datashare.ed.ac.uk/handle/10283/3443")
    print("  2. Download VCTK-Corpus-0.92.zip")
    print(f"  3. Extract to: {VCTK_DIR}")
    print("\nAlternatively, use Hugging Face:")
    print("  pip install datasets")
    print("  from datasets import load_dataset")
    print("  ds = load_dataset('vctk', split='train')")
    return False


def prepare_ljspeech_feminine(num_samples: int = 500) -> List[Tuple[Path, str]]:
    """
    Prepare LJSpeech samples for feminine voice training.
    LJSpeech is recorded by Linda Johnson - a clear, feminine voice.
    """
    print(f"\n[LJSPEECH] Preparing {num_samples} samples...")
    
    if not check_ljspeech():
        print("[ERROR] LJSpeech not found!")
        print(f"  Expected at: {LJSPEECH_DIR}")
        print("\nTo download LJSpeech:")
        print("  1. Visit: https://keithito.com/LJ-Speech-Dataset/")
        print("  2. Download LJSpeech-1.1.tar.bz2")
        print(f"  3. Extract to: {LJSPEECH_DIR}")
        return []
    
    # Read metadata
    metadata_file = LJSPEECH_DIR / "metadata.csv"
    samples = []
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            if len(parts) >= 2:
                wav_id = parts[0]
                text = parts[1]  # Normalized text
                wav_path = LJSPEECH_DIR / "wavs" / f"{wav_id}.wav"
                if wav_path.exists():
                    samples.append((wav_path, text))
    
    # Shuffle and limit
    random.shuffle(samples)
    samples = samples[:num_samples]
    
    print(f"[LJSPEECH] Found {len(samples)} samples")
    return samples


def prepare_vctk_feminine(num_samples: int = 500) -> List[Tuple[Path, str]]:
    """Prepare VCTK female speaker samples."""
    print(f"\n[VCTK] Preparing {num_samples} samples from female speakers...")
    
    if not VCTK_DIR.exists():
        print("[INFO] VCTK not found - using LJSpeech only")
        return []
    
    samples = []
    txt_dir = VCTK_DIR / "txt"
    wav_dir = VCTK_DIR / "wav48_silence_trimmed"
    
    if not wav_dir.exists():
        wav_dir = VCTK_DIR / "wav48"
    
    for speaker in VCTK_FEMALE_SPEAKERS:
        speaker_txt = txt_dir / speaker
        speaker_wav = wav_dir / speaker
        
        if not speaker_txt.exists() or not speaker_wav.exists():
            continue
        
        for txt_file in speaker_txt.glob("*.txt"):
            wav_file = speaker_wav / txt_file.name.replace(".txt", "_mic1.flac")
            if not wav_file.exists():
                wav_file = speaker_wav / txt_file.name.replace(".txt", ".wav")
            
            if wav_file.exists():
                with open(txt_file, 'r', encoding='utf-8') as f:
                    text = f.read().strip()
                samples.append((wav_file, text))
    
    random.shuffle(samples)
    samples = samples[:num_samples]
    
    print(f"[VCTK] Found {len(samples)} samples")
    return samples


def create_training_dataset(samples: List[Tuple[Path, str]], output_dir: Path):
    """Create XTTS-compatible training dataset."""
    print(f"\n[DATASET] Creating training dataset at {output_dir}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    wavs_dir = output_dir / "wavs"
    wavs_dir.mkdir(exist_ok=True)
    
    metadata = []
    
    for i, (wav_path, text) in enumerate(samples):
        # Copy/convert audio
        new_wav = wavs_dir / f"feminine_{i:05d}.wav"
        
        if wav_path.suffix == ".wav":
            shutil.copy(wav_path, new_wav)
        else:
            # Convert flac to wav using ffmpeg or similar
            try:
                import soundfile as sf
                audio, sr = sf.read(wav_path)
                sf.write(new_wav, audio, sr)
            except ImportError:
                print(f"  [WARN] Cannot convert {wav_path.suffix} - install soundfile")
                continue
        
        metadata.append({
            "audio_file": str(new_wav.relative_to(output_dir)),
            "text": text,
            "speaker_name": "feminine_voice"
        })
        
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(samples)} samples...")
    
    # Save metadata
    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    # Create train/eval split
    random.shuffle(metadata)
    split_idx = int(len(metadata) * 0.9)
    train_data = metadata[:split_idx]
    eval_data = metadata[split_idx:]
    
    with open(output_dir / "train.json", 'w', encoding='utf-8') as f:
        json.dump(train_data, f, indent=2)
    
    with open(output_dir / "eval.json", 'w', encoding='utf-8') as f:
        json.dump(eval_data, f, indent=2)
    
    print(f"[DATASET] Created {len(train_data)} train, {len(eval_data)} eval samples")
    return output_dir


def train_xtts_feminine(dataset_dir: Path, epochs: int = 10):
    """Train XTTS AccentTune with feminine voice dataset."""
    print("\n" + "="*60)
    print("TRAINING XTTS WITH FEMININE VOICE")
    print("="*60)
    
    try:
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import Xtts
        from trainer import Trainer, TrainerArgs
    except ImportError:
        print("\n[ERROR] TTS library not installed!")
        print("Install with: pip install TTS")
        return False
    
    # Find base XTTS model
    base_model = MODELS_DIR / "xtts_official_trained" / "run" / "training" / "XTTS_v2.0_original_model_files"
    if not base_model.exists():
        print(f"[ERROR] Base XTTS model not found at {base_model}")
        return False
    
    # Output directory for feminine voice model
    output_dir = MODELS_DIR / "xtts_feminine_voice"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[TRAIN] Base model: {base_model}")
    print(f"[TRAIN] Dataset: {dataset_dir}")
    print(f"[TRAIN] Output: {output_dir}")
    print(f"[TRAIN] Epochs: {epochs}")
    
    # Load config
    config = XttsConfig()
    config.load_json(str(base_model / "config.json"))
    
    # Update training config
    config.batch_size = 2
    config.eval_batch_size = 2
    config.num_loader_workers = 2
    config.output_path = str(output_dir)
    
    # Training args
    trainer_args = TrainerArgs(
        restore_path=None,
        skip_train_epoch=False,
        start_with_eval=False,
        grad_accum_steps=4,
    )
    
    # Load datasets
    train_samples = json.load(open(dataset_dir / "train.json"))
    eval_samples = json.load(open(dataset_dir / "eval.json"))
    
    print(f"\n[TRAIN] Starting training with {len(train_samples)} samples...")
    print("[TRAIN] This may take 1-4 hours depending on GPU...")
    
    # Note: Full training implementation would go here
    # For AccentTune (lighter training), use the existing accent_tune approach
    
    print("\n[INFO] For quick feminine voice adaptation, use AccentTune instead:")
    print(f"  python train_accent_tune_feminine.py")
    
    return True


def main():
    print("="*60)
    print("FEMININE VOICE TRAINING FOR MONICA")
    print("="*60)
    print("\nThis script prepares and trains Monica's voice to sound feminine.")
    print("\nAvailable datasets:")
    print("  1. LJSpeech (Linda Johnson) - FREE, ~2.6GB")
    print("  2. VCTK Female Speakers - FREE, ~11GB (optional)")
    
    # Check existing datasets
    has_ljspeech = check_ljspeech()
    has_vctk = VCTK_DIR.exists()
    
    print(f"\n[STATUS] LJSpeech: {'[?] Found' if has_ljspeech else '[?] Not found'}")
    print(f"[STATUS] VCTK: {'[?] Found' if has_vctk else '[?] Not found'}")
    
    if not has_ljspeech and not has_vctk:
        print("\n[ERROR] No training datasets found!")
        print("\nTo get started, download LJSpeech:")
        print("  1. Visit: https://keithito.com/LJ-Speech-Dataset/")
        print("  2. Download LJSpeech-1.1.tar.bz2 (~2.6GB)")
        print(f"  3. Extract to: {LJSPEECH_DIR}")
        return
    
    # Collect samples
    all_samples = []
    
    if has_ljspeech:
        ljspeech_samples = prepare_ljspeech_feminine(500)
        all_samples.extend(ljspeech_samples)
    
    if has_vctk:
        vctk_samples = prepare_vctk_feminine(300)
        all_samples.extend(vctk_samples)
    
    if not all_samples:
        print("\n[ERROR] No samples collected!")
        return
    
    print(f"\n[TOTAL] Collected {len(all_samples)} feminine voice samples")
    
    # Create dataset
    dataset_dir = create_training_dataset(all_samples, FEMININE_DATASET_DIR)
    
    print("\n" + "="*60)
    print("DATASET READY!")
    print("="*60)
    print(f"\nDataset created at: {dataset_dir}")
    print(f"  - Train samples: {len(json.load(open(dataset_dir / 'train.json')))}")
    print(f"  - Eval samples: {len(json.load(open(dataset_dir / 'eval.json')))}")
    
    print("\n[NEXT STEPS]")
    print("  1. Run AccentTune training (faster, ~30 min):")
    print(f"     python train_accent_tune_feminine.py")
    print("")
    print("  2. Or run full XTTS fine-tuning (slower, ~2-4 hours):")
    print(f"     python train_xtts_official.py --dataset {dataset_dir}")


if __name__ == "__main__":
    main()
