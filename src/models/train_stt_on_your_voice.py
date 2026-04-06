#!/usr/bin/env python3
"""
Train STT Model on YOUR 4,217 Voice Recordings
===============================================
This script fine-tunes wav2vec2 on your actual voice recordings
located in: data/training/recordings/wake_phrases/

Your recordings have transcripts embedded in filenames like:
  0001_The_quick_brown_fox_jumps_over_the_lazy_dog.wav
  phrase_0828_20251216_191810_The_meeting_is_scheduled_.wav
"""

import os
import sys

# Prevent peft from being imported (causes version conflict)
sys.modules['peft'] = None

import re
import json
import torch
import numpy as np
import librosa
from pathlib import Path
from dataclasses import dataclass
from typing import Union
from datetime import datetime

print("=" * 70)
print("TRAINING STT ON YOUR 4,217 VOICE RECORDINGS")
print("=" * 70)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
TRAINING_ROOT = PROJECT_ROOT / "data" / "training"
RECORDINGS_DIR = TRAINING_ROOT / "recordings" / "wake_phrases"
BASE_MODEL = PROJECT_ROOT / "models" / "wav2vec2_final" / "final_model"
OUTPUT_DIR = PROJECT_ROOT / "models" / "wav2vec2_your_voice"

# Training params
LEARNING_RATE = 5e-6  # Very low for fine-tuning
EPOCHS = 5
BATCH_SIZE = 4
GRAD_ACCUM = 4
WARMUP_STEPS = 200
SAMPLE_RATE = 16000

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def extract_transcript_from_filename(filename: str) -> str:
    """Extract transcript from filename."""
    name = Path(filename).stem
    
    # Pattern 1: 0001_The_quick_brown_fox.wav
    if re.match(r'^\d{4}_', name):
        text = name[5:]  # Remove "0001_"
        text = text.replace('_', ' ')
        return clean_text(text)
    
    # Pattern 2: phrase_0828_20251216_191810_The_meeting_is_scheduled_.wav
    if name.startswith('phrase_'):
        parts = name.split('_')
        if len(parts) >= 5:
            # Skip: phrase, number, date, time
            text = '_'.join(parts[4:])
            text = text.replace('_', ' ')
            return clean_text(text)
    
    # Fallback: just replace underscores
    text = name.replace('_', ' ')
    return clean_text(text)

def clean_text(text: str) -> str:
    """Clean text for wav2vec2 (uppercase, letters + space only)."""
    text = text.upper()
    text = text.replace("'", "").replace("'", "").replace("-", " ")
    text = re.sub(r'[^A-Z ]', '', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

def main():
    # Check recordings exist
    if not RECORDINGS_DIR.exists():
        print(f"ERROR: Recordings directory not found: {RECORDINGS_DIR}")
        return
    
    wav_files = list(RECORDINGS_DIR.glob("*.wav"))
    print(f"\nFound {len(wav_files)} WAV files in {RECORDINGS_DIR}")
    
    if len(wav_files) == 0:
        print("ERROR: No WAV files found!")
        return
    
    # Load base model
    print(f"\nLoading base model from: {BASE_MODEL}")
    
    from transformers import (
        Wav2Vec2Processor,
        Wav2Vec2ForCTC,
        TrainingArguments,
        Trainer
    )
    from datasets import Dataset
    import soundfile as sf
    
    if not BASE_MODEL.exists():
        print(f"ERROR: Base model not found at {BASE_MODEL}")
        print("Using pretrained facebook/wav2vec2-base-960h instead")
        model_name = "facebook/wav2vec2-base-960h"
    else:
        model_name = str(BASE_MODEL)
    
    processor = Wav2Vec2Processor.from_pretrained(model_name)
    print(f"Loaded processor with vocab size: {len(processor.tokenizer)}")
    
    # Prepare data
    print("\nPreparing training data...")
    data = []
    skipped = 0
    
    for i, wav_file in enumerate(wav_files):
        if i % 500 == 0:
            print(f"  Processing {i}/{len(wav_files)}...")
        
        try:
            # Get transcript from filename
            text = extract_transcript_from_filename(wav_file.name)
            
            if not text or len(text) < 2:
                skipped += 1
                continue
            
            # Check audio duration
            info = sf.info(str(wav_file))
            if info.duration < 0.5 or info.duration > 30:
                skipped += 1
                continue
            
            data.append({
                "path": str(wav_file),
                "text": text,
                "duration": info.duration
            })
            
        except Exception as e:
            skipped += 1
            continue
    
    print(f"\nValid recordings: {len(data)}")
    print(f"Skipped: {skipped}")
    
    if len(data) < 10:
        print("ERROR: Not enough valid recordings!")
        return
    
    total_hours = sum(d["duration"] for d in data) / 3600
    print(f"Total audio: {total_hours:.2f} hours")
    
    # Show samples
    print("\nSample transcripts:")
    for d in data[:5]:
        print(f"  {Path(d['path']).name[:40]}... -> '{d['text'][:50]}'")
    
    # Shuffle and split
    import random
    random.seed(42)
    random.shuffle(data)
    
    split_idx = int(len(data) * 0.95)  # 95% train, 5% val
    train_data = data[:split_idx]
    val_data = data[split_idx:]
    
    print(f"\nTrain: {len(train_data)}, Validation: {len(val_data)}")
    
    # Prepare datasets
    print("\nLoading audio and tokenizing...")
    
    def load_and_prepare(data_list, name="dataset"):
        prepared = []
        for i, item in enumerate(data_list):
            if i % 200 == 0:
                print(f"  {name}: {i}/{len(data_list)}")
            try:
                audio, sr = librosa.load(item["path"], sr=SAMPLE_RATE)
                input_values = processor(audio, sampling_rate=SAMPLE_RATE).input_values[0]
                labels = processor.tokenizer(item["text"]).input_ids
                
                if len(labels) > 0 and len(input_values) > 0:
                    prepared.append({"input_values": input_values, "labels": labels})
            except Exception as e:
                continue
        return prepared
    
    train_prepared = load_and_prepare(train_data, "train")
    val_prepared = load_and_prepare(val_data, "val")
    
    print(f"\nPrepared - Train: {len(train_prepared)}, Val: {len(val_prepared)}")
    
    if len(train_prepared) < 10:
        print("ERROR: Not enough prepared data!")
        return
    
    train_dataset = Dataset.from_dict({
        "input_values": [p["input_values"] for p in train_prepared],
        "labels": [p["labels"] for p in train_prepared]
    })
    val_dataset = Dataset.from_dict({
        "input_values": [p["input_values"] for p in val_prepared],
        "labels": [p["labels"] for p in val_prepared]
    })
    
    # Data collator
    @dataclass
    class DataCollatorCTCWithPadding:
        processor: Wav2Vec2Processor
        padding: Union[bool, str] = True
        
        def __call__(self, features):
            input_features = [{"input_values": f["input_values"]} for f in features]
            label_features = [{"input_ids": f["labels"]} for f in features]
            
            batch = self.processor.pad(input_features, padding=self.padding, return_tensors="pt")
            
            with self.processor.as_target_processor():
                labels_batch = self.processor.pad(label_features, padding=self.padding, return_tensors="pt")
            
            labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)
            batch["labels"] = labels
            return batch
    
    data_collator = DataCollatorCTCWithPadding(processor=processor)
    
    # Load model
    print("\nLoading model for fine-tuning...")
    model = Wav2Vec2ForCTC.from_pretrained(model_name)
    model.freeze_feature_extractor()
    print("[?] Feature extractor frozen (only fine-tuning decoder)")
    
    # Metrics
    import evaluate
    wer_metric = evaluate.load("wer")
    
    def compute_metrics(pred):
        pred_logits = pred.predictions
        pred_ids = np.argmax(pred_logits, axis=-1)
        pred.label_ids[pred.label_ids == -100] = processor.tokenizer.pad_token_id
        
        pred_str = processor.batch_decode(pred_ids)
        label_str = processor.batch_decode(pred.label_ids, group_tokens=False)
        
        if len(pred_str) > 0:
            print(f"\n  [SAMPLE] Pred: '{pred_str[0][:50]}' | Label: '{label_str[0][:50]}'")
        
        wer = wer_metric.compute(predictions=pred_str, references=label_str)
        return {"wer": wer}
    
    # Training args
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        group_by_length=True,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        eval_strategy="steps",
        eval_steps=100,
        save_steps=200,
        logging_steps=50,
        learning_rate=LEARNING_RATE,
        warmup_steps=WARMUP_STEPS,
        num_train_epochs=EPOCHS,
        fp16=torch.cuda.is_available(),
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        dataloader_num_workers=0,
        report_to="none",
        max_grad_norm=1.0,
    )
    
    trainer = Trainer(
        model=model,
        data_collator=data_collator,
        args=training_args,
        compute_metrics=compute_metrics,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=processor.feature_extractor,
    )
    
    # Train
    print("\n" + "=" * 70)
    print(f"STARTING TRAINING")
    print(f"  Recordings: {len(train_prepared)}")
    print(f"  Epochs: {EPOCHS}")
    print(f"  Learning rate: {LEARNING_RATE}")
    print(f"  Batch size: {BATCH_SIZE} x {GRAD_ACCUM} = {BATCH_SIZE * GRAD_ACCUM}")
    print(f"  GPU: {torch.cuda.is_available()}")
    print("=" * 70 + "\n")
    
    trainer.train()
    
    # Save
    print("\n" + "=" * 70)
    print("SAVING MODEL")
    print("=" * 70)
    
    final_path = OUTPUT_DIR / "final_model"
    final_path.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(final_path))
    processor.save_pretrained(str(final_path))
    
    results = trainer.evaluate()
    
    print(f"\n{'=' * 70}")
    print(f"TRAINING COMPLETE!")
    print(f"Final WER: {results['eval_wer']*100:.2f}%")
    print(f"Model saved to: {final_path}")
    print(f"{'=' * 70}")
    
    # Instructions
    print("\n" + "=" * 70)
    print("TO USE THIS MODEL:")
    print("=" * 70)
    print(f"Update speechbrain_final.py to use:")
    print(f'  trained_model_path = project_root / "models" / "wav2vec2_your_voice" / "final_model"')
    print("=" * 70)


if __name__ == "__main__":
    main()
