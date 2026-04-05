#!/usr/bin/env python3
"""
Continue Training Monica's Voice Model
Resumes from the last checkpoint to improve accuracy (WER 50% -> lower)
"""

import os
import sys
from pathlib import Path
import torch
import torchaudio
from datasets import Dataset
import pandas as pd
from transformers import (
    Wav2Vec2ForCTC,
    Wav2Vec2Processor,
    TrainingArguments,
    Trainer,
)
from dataclasses import dataclass
from typing import Dict, List, Union
import numpy as np
import evaluate

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent  # Go up from scripts/ to project root
TRAIN_CSV = PROJECT_ROOT / "data" / "training" / "datasets" / "stt_combined" / "train.csv"
VAL_CSV = PROJECT_ROOT / "data" / "training" / "datasets" / "stt_combined" / "val.csv"
OUTPUT_DIR = PROJECT_ROOT / "models" / "wav2vec2_your_voice"
FINAL_MODEL_DIR = OUTPUT_DIR / "final_model"

# Pick latest checkpoint if available; otherwise use final_model.
checkpoint_dirs = []
if OUTPUT_DIR.exists():
    checkpoint_dirs = sorted(
        [p for p in OUTPUT_DIR.glob("checkpoint-*") if p.is_dir()],
        key=lambda p: int(p.name.split("-")[-1]) if p.name.split("-")[-1].isdigit() else -1
    )
CHECKPOINT_DIR = checkpoint_dirs[-1] if checkpoint_dirs else FINAL_MODEL_DIR

# Training hyperparameters - LOWER learning rate for fine-tuning
LEARNING_RATE = 1e-4  # Even lower for continued training
NUM_EPOCHS = 50  # More epochs
BATCH_SIZE = 4
GRADIENT_ACCUMULATION = 4
WARMUP_STEPS = 100
SAVE_STEPS = 200
EVAL_STEPS = 200

print("=" * 80)
print("MONICA VOICE MODEL - CONTINUED TRAINING")
print("=" * 80)
print(f"Resuming from: {CHECKPOINT_DIR}")
print(f"Learning rate: {LEARNING_RATE}")
print(f"Additional epochs: {NUM_EPOCHS}")
print("=" * 80)

# Load processor from the trained model
print("\n[1/5] Loading processor and model...")
processor = Wav2Vec2Processor.from_pretrained(str(FINAL_MODEL_DIR))

# Load model from checkpoint
if CHECKPOINT_DIR.exists():
    print(f"  Loading from checkpoint: {CHECKPOINT_DIR}")
    model = Wav2Vec2ForCTC.from_pretrained(str(CHECKPOINT_DIR))
else:
    print(f"  Checkpoint not found, loading from final_model")
    model = Wav2Vec2ForCTC.from_pretrained(str(FINAL_MODEL_DIR))

# Freeze feature extractor
model.freeze_feature_extractor()
print("  Feature extractor frozen")

# Load training data
print("\n[2/5] Loading training data...")
train_df = pd.read_csv(TRAIN_CSV)
val_df = pd.read_csv(VAL_CSV)
print(f"  Training samples: {len(train_df)}")
print(f"  Validation samples: {len(val_df)}")

# Prepare datasets
print("\n[3/5] Preparing datasets...")

def load_audio(row):
    """Load and resample audio to 16kHz"""
    wav_path = row["wav"]
    if not os.path.exists(wav_path):
        wav_path = wav_path.replace("C:/Monica", str(PROJECT_ROOT))
    
    waveform, sample_rate = torchaudio.load(wav_path)
    
    if sample_rate != 16000:
        resampler = torchaudio.transforms.Resample(sample_rate, 16000)
        waveform = resampler(waveform)
    
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
    
    inputs = processor(
        audio["array"],
        sampling_rate=audio["sampling_rate"],
        return_tensors="pt",
        padding=True,
    )
    
    batch["input_values"] = inputs.input_values[0]
    batch["attention_mask"] = inputs.attention_mask[0] if "attention_mask" in inputs else None
    
    with processor.as_target_processor():
        batch["labels"] = processor(batch["text"]).input_ids
    
    return batch

print("\n[4/5] Preprocessing datasets...")
train_dataset = train_dataset.map(preprocess_function, remove_columns=["audio", "text"])
val_dataset = val_dataset.map(preprocess_function, remove_columns=["audio", "text"])

# Data collator
@dataclass
class DataCollatorCTCWithPadding:
    processor: Wav2Vec2Processor
    padding: Union[bool, str] = True

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
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

        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)
        batch["labels"] = labels

        return batch

data_collator = DataCollatorCTCWithPadding(processor=processor, padding=True)

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

# Training arguments
training_args = TrainingArguments(
    output_dir=str(OUTPUT_DIR),
    group_by_length=True,
    per_device_train_batch_size=BATCH_SIZE,
    gradient_accumulation_steps=GRADIENT_ACCUMULATION,
    eval_strategy="steps",
    num_train_epochs=NUM_EPOCHS,
    gradient_checkpointing=True,
    fp16=torch.cuda.is_available(),
    save_steps=SAVE_STEPS,
    eval_steps=EVAL_STEPS,
    logging_steps=50,
    learning_rate=LEARNING_RATE,
    warmup_steps=WARMUP_STEPS,
    save_total_limit=3,
    load_best_model_at_end=True,
    metric_for_best_model="wer",
    greater_is_better=False,
    report_to="none",
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
print("\n[5/5] Starting continued training...")
print("=" * 80)
print(f"  Learning rate: {LEARNING_RATE}")
print(f"  Epochs: {NUM_EPOCHS}")
print(f"  Target: WER < 30%")
print("=" * 80 + "\n")

trainer.train()

# Save final model
print("\n[DONE] Saving improved model...")
trainer.save_model(str(OUTPUT_DIR / "final_model"))
processor.save_pretrained(str(OUTPUT_DIR / "final_model"))

print("\n" + "=" * 80)
print("CONTINUED TRAINING COMPLETE!")
print("=" * 80)
print(f"Model saved to: {OUTPUT_DIR / 'final_model'}")
print("Restart Monica to use the improved model.")
print("=" * 80)
