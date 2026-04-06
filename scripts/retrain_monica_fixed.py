#!/usr/bin/env python3
"""
FIXED Training Script for Monica's Custom Voice Model
Based on HuggingFace best practices for small dataset fine-tuning

This script properly trains wav2vec2 on YOUR 1,113 voice recordings.
The previous training failed (WER 100%) due to improper hyperparameters.

Key fixes:
1. Lower learning rate (3e-4 instead of 0.5)
2. All dropout set to 0.0 for small datasets
3. Freeze feature extractor (CNN layers)
4. More epochs with warmup
5. Proper gradient accumulation

To run:
    python retrain_monica_fixed.py

Author: Fixed based on HuggingFace and SpeechBrain best practices
"""

import os
import sys
from pathlib import Path
import torch
import torchaudio
from datasets import Dataset, Audio
import pandas as pd
from transformers import (
    Wav2Vec2ForCTC,
    Wav2Vec2Processor,
    Wav2Vec2CTCTokenizer,
    Wav2Vec2FeatureExtractor,
    TrainingArguments,
    Trainer,
)
from dataclasses import dataclass
from typing import Dict, List, Union
import numpy as np
import evaluate

# Configuration
PROJECT_ROOT = Path(__file__).parent
TRAIN_CSV = PROJECT_ROOT / "voice_training" / "recordings" / "MJP" / "train.csv"
VAL_CSV = PROJECT_ROOT / "voice_training" / "recordings" / "MJP" / "val.csv"
OUTPUT_DIR = PROJECT_ROOT / "models" / "monica_wav2vec2_fixed"
VOCAB_FILE = OUTPUT_DIR / "vocab.json"

# Training hyperparameters (FIXED for small dataset)
LEARNING_RATE = 3e-4  # Much lower than before (was 0.5!)
NUM_EPOCHS = 30  # More epochs for small dataset
BATCH_SIZE = 4  # Small batch for GPU memory
GRADIENT_ACCUMULATION = 4  # Effective batch size = 16
WARMUP_STEPS = 500
SAVE_STEPS = 200
EVAL_STEPS = 200

print("=" * 80)
print("MONICA VOICE MODEL RETRAINING - FIXED VERSION")
print("=" * 80)
print(f"Training data: {TRAIN_CSV}")
print(f"Validation data: {VAL_CSV}")
print(f"Output directory: {OUTPUT_DIR}")
print(f"Learning rate: {LEARNING_RATE}")
print(f"Epochs: {NUM_EPOCHS}")
print("=" * 80)

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load training data
print("\n[1/6] Loading training data...")
train_df = pd.read_csv(TRAIN_CSV)
val_df = pd.read_csv(VAL_CSV)

print(f"  Training samples: {len(train_df)}")
print(f"  Validation samples: {len(val_df)}")

# Create vocabulary from transcriptions
print("\n[2/6] Creating vocabulary...")
all_text = " ".join(train_df["wrd"].tolist() + val_df["wrd"].tolist())
vocab_list = list(set(all_text.lower()))
vocab_dict = {v: k for k, v in enumerate(sorted(vocab_list))}

# Add special tokens
vocab_dict["[UNK]"] = len(vocab_dict)
vocab_dict["[PAD]"] = len(vocab_dict)
vocab_dict["|"] = vocab_dict.get(" ", len(vocab_dict))  # Word boundary

print(f"  Vocabulary size: {len(vocab_dict)}")

# Save vocabulary
import json
with open(VOCAB_FILE, "w") as f:
    json.dump(vocab_dict, f)

# Create tokenizer and feature extractor
print("\n[3/6] Creating tokenizer and feature extractor...")
tokenizer = Wav2Vec2CTCTokenizer(
    str(VOCAB_FILE),
    unk_token="[UNK]",
    pad_token="[PAD]",
    word_delimiter_token="|",
)

feature_extractor = Wav2Vec2FeatureExtractor(
    feature_size=1,
    sampling_rate=16000,
    padding_value=0.0,
    do_normalize=True,
    return_attention_mask=True,
)

processor = Wav2Vec2Processor(
    feature_extractor=feature_extractor,
    tokenizer=tokenizer,
)

# Save processor
processor.save_pretrained(str(OUTPUT_DIR))

# Prepare datasets
print("\n[4/6] Preparing datasets...")

def load_audio(row):
    """Load and resample audio to 16kHz"""
    wav_path = row["wav"]
    if not os.path.exists(wav_path):
        # Try relative path from project root
        wav_path = wav_path.replace("C:/Monica", str(PROJECT_ROOT))
    
    waveform, sample_rate = torchaudio.load(wav_path)
    
    # Resample to 16kHz if needed
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(sample_rate, 16000)
        waveform = resampler(waveform)
    
    # Convert to mono if stereo
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)
    
    return waveform.squeeze().numpy()

def prepare_dataset(df):
    """Prepare dataset for training"""
    data = []
    for idx, row in df.iterrows():
        try:
            audio = load_audio(row)
            text = row["wrd"].lower()
            data.append({
                "audio": {"array": audio, "sampling_rate": 16000},
                "text": text,
            })
        except Exception as e:
            print(f"  Warning: Could not load {row['wav']}: {e}")
    return Dataset.from_list(data)

train_dataset = prepare_dataset(train_df)
val_dataset = prepare_dataset(val_df)

print(f"  Loaded {len(train_dataset)} training samples")
print(f"  Loaded {len(val_dataset)} validation samples")

# Preprocess function
def preprocess_function(batch):
    audio = batch["audio"]
    
    # Process audio
    inputs = processor(
        audio["array"],
        sampling_rate=audio["sampling_rate"],
        return_tensors="pt",
        padding=True,
    )
    
    batch["input_values"] = inputs.input_values[0]
    batch["attention_mask"] = inputs.attention_mask[0] if "attention_mask" in inputs else None
    
    # Process text
    with processor.as_target_processor():
        batch["labels"] = processor(batch["text"]).input_ids
    
    return batch

print("\n[5/6] Preprocessing datasets...")
train_dataset = train_dataset.map(preprocess_function, remove_columns=["audio", "text"])
val_dataset = val_dataset.map(preprocess_function, remove_columns=["audio", "text"])

# Data collator
@dataclass
class DataCollatorCTCWithPadding:
    processor: Wav2Vec2Processor
    padding: Union[bool, str] = True

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        # Split inputs and labels
        input_features = [{"input_values": feature["input_values"]} for feature in features]
        label_features = [{"input_ids": feature["labels"]} for feature in features]

        batch = self.processor.pad(
            input_features,
            padding=self.padding,
            return_tensors="pt",
        )

        with self.processor.as_target_processor():
            labels_batch = self.processor.pad(
                label_features,
                padding=self.padding,
                return_tensors="pt",
            )

        # Replace padding with -100 for loss calculation
        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)
        batch["labels"] = labels

        return batch

data_collator = DataCollatorCTCWithPadding(processor=processor, padding=True)

# Load model with FIXED settings for small dataset
print("\n[6/6] Loading model with FIXED hyperparameters...")
model = Wav2Vec2ForCTC.from_pretrained(
    "facebook/wav2vec2-base-960h",
    attention_dropout=0.0,  # FIXED: No dropout for small dataset
    hidden_dropout=0.0,     # FIXED: No dropout for small dataset
    feat_proj_dropout=0.0,  # FIXED: No dropout for small dataset
    mask_time_prob=0.05,    # FIXED: Lower masking
    layerdrop=0.0,          # FIXED: No layer dropout
    ctc_loss_reduction="mean",
    pad_token_id=processor.tokenizer.pad_token_id,
    vocab_size=len(processor.tokenizer),
)

# CRITICAL: Freeze feature extractor (CNN layers) - they don't need fine-tuning
model.freeze_feature_extractor()
print("  Feature extractor frozen (CNN layers)")

# Compute metrics
wer_metric = evaluate.load("wer")

def compute_metrics(pred):
    pred_logits = pred.predictions
    pred_ids = np.argmax(pred_logits, axis=-1)

    pred.label_ids[pred.label_ids == -100] = processor.tokenizer.pad_token_id

    pred_str = processor.batch_decode(pred_ids)
    label_str = processor.batch_decode(pred.label_ids, group_tokens=False)

    wer = wer_metric.compute(predictions=pred_str, references=label_str)

    return {"wer": wer}

# Training arguments with FIXED settings
training_args = TrainingArguments(
    output_dir=str(OUTPUT_DIR),
    group_by_length=True,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUMULATION,
    eval_strategy="steps",
    num_train_epochs=NUM_EPOCHS,
    gradient_checkpointing=True,
    fp16=True,
    save_steps=SAVE_STEPS,
    eval_steps=EVAL_STEPS,
    logging_steps=50,
    learning_rate=LEARNING_RATE,
    warmup_steps=WARMUP_STEPS,
    save_total_limit=3,
    load_best_model_at_end=True,
    metric_for_best_model="wer",
    greater_is_better=False,
    report_to="none",  # Disable wandb/tensorboard
)

# Create trainer
trainer = Trainer(
    model=model,
    data_collator=data_collator,
    args=training_args,
    compute_metrics=compute_metrics,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    tokenizer=processor.feature_extractor,
)

# Start training
print("\n" + "=" * 80)
print("STARTING TRAINING - This will take some time...")
print("=" * 80)
print(f"  Learning rate: {LEARNING_RATE}")
print(f"  Epochs: {NUM_EPOCHS}")
print(f"  Batch size: {BATCH_SIZE} x {GRADIENT_ACCUMULATION} = {BATCH_SIZE * GRADIENT_ACCUMULATION}")
print(f"  Warmup steps: {WARMUP_STEPS}")
print("=" * 80 + "\n")

trainer.train()

# Save final model
print("\n[DONE] Saving final model...")
trainer.save_model(str(OUTPUT_DIR / "final_model"))
processor.save_pretrained(str(OUTPUT_DIR / "final_model"))

print("\n" + "=" * 80)
print("TRAINING COMPLETE!")
print("=" * 80)
print(f"Model saved to: {OUTPUT_DIR / 'final_model'}")
print("\nTo use this model in Monica, update the config to point to:")
print(f"  {OUTPUT_DIR / 'final_model'}")
print("=" * 80)
