#!/usr/bin/env python3
"""
Create SentencePiece Tokenizer for Monica Voice Training

This script creates a SentencePiece tokenizer from the training transcriptions.
SentencePiece is required because CTCTextEncoder fails with small datasets.

Based on SpeechBrain CommonVoice recipe tokenizer approach.
"""

import os
import sys
from pathlib import Path
import json

def main():
    print("=" * 80)
    print("MONICA SENTENCEPIECE TOKENIZER CREATOR")
    print("=" * 80)
    
    # Paths
    project_root = Path(__file__).parent
    recordings_dir = project_root / "voice_training" / "recordings" / "MJP"
    train_csv = recordings_dir / "train.csv"
    tokenizer_dir = project_root / "models" / "monica_tokenizer"
    tokenizer_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[1/4] Reading training transcriptions from: {train_csv}")
    
    if not train_csv.exists():
        print(f"[X] Error: Training CSV not found at {train_csv}")
        print("Please ensure you have recorded voice samples first.")
        sys.exit(1)
    
    # Read all transcriptions from train.csv
    transcriptions = []
    with open(train_csv, 'r', encoding='utf-8') as f:
        lines = f.readlines()[1:]  # Skip header
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) >= 4:
                # CSV format: ID,duration,wav,wrd
                transcription = parts[3].strip()
                if transcription:
                    transcriptions.append(transcription)
    
    print(f"[OK] Found {len(transcriptions)} transcriptions")
    
    if len(transcriptions) < 100:
        print(f"[WARN]  Warning: Only {len(transcriptions)} transcriptions found.")
        print("SentencePiece works best with more data, but will proceed.")
    
    # Write transcriptions to temporary text file for SentencePiece
    print("\n[2/4] Creating temporary text file for SentencePiece training...")
    temp_text_file = tokenizer_dir / "transcriptions.txt"
    with open(temp_text_file, 'w', encoding='utf-8') as f:
        for text in transcriptions:
            f.write(text.lower() + '\n')  # Lowercase for consistency
    
    print(f"[OK] Wrote {len(transcriptions)} lines to {temp_text_file}")
    
    # Train SentencePiece model
    print("\n[3/4] Training SentencePiece tokenizer...")
    try:
        import sentencepiece as spm
    except ImportError:
        print("[X] Error: sentencepiece not installed")
        print("Install with: pip install sentencepiece")
        sys.exit(1)
    
    # SentencePiece training parameters
    # vocab_size: Small for character-level-like behavior with small dataset
    # character_coverage: 1.0 for English (covers all characters)
    # model_type: unigram (better for small datasets than BPE)
    vocab_size = 1000  # Small vocab for 1,113 recordings
    model_prefix = str(tokenizer_dir / "monica_1000")
    
    spm.SentencePieceTrainer.train(
        input=str(temp_text_file),
        model_prefix=model_prefix,
        vocab_size=vocab_size,
        character_coverage=1.0,
        model_type='unigram',
        pad_id=0,
        unk_id=1,
        bos_id=2,
        eos_id=3,
        pad_piece='<pad>',
        unk_piece='<unk>',
        bos_piece='<bos>',
        eos_piece='<eos>',
        user_defined_symbols=['<blank>'],  # CTC blank token
        normalization_rule_name='nmt_nfkc_cf',  # Normalize text
    )
    
    print(f"[OK] SentencePiece model trained: {model_prefix}.model")
    print(f"   Vocabulary size: {vocab_size}")
    
    # Test the tokenizer
    print("\n[4/4] Testing tokenizer...")
    sp = spm.SentencePieceProcessor()
    sp.load(f"{model_prefix}.model")
    
    test_phrases = [
        "monica initialize",
        "hello monica",
        "what is the weather today",
        "stop listening"
    ]
    
    print("\nTest tokenization:")
    for phrase in test_phrases:
        tokens = sp.encode(phrase, out_type=str)
        ids = sp.encode(phrase, out_type=int)
        print(f"  '{phrase}'")
        print(f"    → Tokens: {tokens[:10]}{'...' if len(tokens) > 10 else ''}")
        print(f"    → IDs: {ids[:10]}{'...' if len(ids) > 10 else ''}")
    
    # Save tokenizer info
    info = {
        "vocab_size": vocab_size,
        "model_type": "unigram",
        "num_training_samples": len(transcriptions),
        "model_path": f"{model_prefix}.model",
        "vocab_path": f"{model_prefix}.vocab",
        "created": str(Path(f"{model_prefix}.model").stat().st_mtime),
    }
    
    info_file = tokenizer_dir / "tokenizer_info.json"
    with open(info_file, 'w') as f:
        json.dump(info, f, indent=2)
    
    print(f"\n[OK] Tokenizer info saved to: {info_file}")
    
    # Clean up temporary file
    temp_text_file.unlink()
    
    print("\n" + "=" * 80)
    print("[OK] SENTENCEPIECE TOKENIZER CREATED SUCCESSFULLY")
    print("=" * 80)
    print(f"\nTokenizer files:")
    print(f"  • Model: {model_prefix}.model")
    print(f"  • Vocab: {model_prefix}.vocab")
    print(f"  • Info: {info_file}")
    print(f"\nNext steps:")
    print(f"  1. hparams_monica.yaml will be updated automatically")
    print(f"  2. Run training from the Voice Training GUI")
    print(f"  3. Model will train correctly with SentencePiece tokenizer")
    print()

if __name__ == "__main__":
    main()
