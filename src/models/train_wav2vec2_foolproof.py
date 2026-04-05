"""
FOOLPROOF Wav2Vec2 Fine-tuning Script for Personal Voice Training
Based on HuggingFace official tutorial + community fixes for WER 100% issue

KEY FIXES FOR WER 100% / BLANK PREDICTIONS:
1. FREEZE feature extractor (CNN layers) - critical for small datasets
2. LOW learning rate (3e-5) - prevents collapse to blank predictions  
3. PROPER vocabulary - only characters in dataset, no unknown tokens
4. CORRECT data collation - labels padded with -100
5. warmup_steps to stabilize early training

Author: Cascade AI
Date: 2024-12-14
"""

if __name__ == "__main__":
    import os
    import json
    import re
    import torch
    import numpy as np
    import soundfile as sf
    from dataclasses import dataclass
    from typing import Any, Dict, List, Union
    from pathlib import Path
    
    print("="*70)
    print("FOOLPROOF WAV2VEC2 FINE-TUNING FOR PERSONAL VOICE")
    print("="*70)
    
    # ============== CONFIGURATION ==============
    PROJECT_DIR = Path("C:/Monica")
    RECORDINGS_DIR = PROJECT_DIR / "data" / "training" / "voice_training" / "recordings" / "MJP"
    OUTPUT_DIR = PROJECT_DIR / "models" / "wav2vec2_personal"
    
    # Model - using base model (smaller, works better with limited data)
    MODEL_NAME = "facebook/wav2vec2-base-960h"
    SAMPLING_RATE = 16000
    
    # CRITICAL: Low learning rate to prevent blank collapse
    LEARNING_RATE = 3e-5  # Very low - key fix for WER 100%
    EPOCHS = 15
    BATCH_SIZE = 4
    GRAD_ACCUM = 2
    WARMUP_STEPS = 200  # Stabilize early training
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # ============== STEP 1: LOAD AND PREPARE DATA ==============
    print("\n[STEP 1] Loading recordings...")
    
    def clean_text(text):
        """Clean text to only a-z and space - CRITICAL for vocab matching"""
        text = text.lower()
        text = text.replace("'", "").replace("'", "")
        text = re.sub(r'[^a-z ]', '', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()
    
    def extract_text_from_filename(filename):
        """Extract transcription from filename"""
        name = Path(filename).stem
        # Handle both formats:
        # GUI: phrase_0004_20251209_231418_Monica_wake_up.wav
        # Terminal: 0001_The_quick_brown_fox.wav
        
        if name.startswith("phrase_"):
            parts = name.split("_")
            if len(parts) >= 5:
                text = " ".join(parts[4:])
                return clean_text(text)
        else:
            parts = name.split("_", 1)
            if len(parts) > 1:
                text = parts[1].replace("_", " ")
                return clean_text(text)
        return clean_text(name.replace("_", " "))
    
    # Load all recordings
    wav_files = list(RECORDINGS_DIR.glob("*.wav"))
    print(f"   Found {len(wav_files)} WAV files")
    
    data = []
    for wav_file in wav_files:
        text = extract_text_from_filename(wav_file.name)
        if text and len(text) >= 2:
            try:
                info = sf.info(str(wav_file))
                if 0.5 <= info.duration <= 20:
                    data.append({
                        "path": str(wav_file),
                        "text": text,
                        "duration": info.duration
                    })
            except:
                pass
    
    print(f"   Valid recordings: {len(data)}")
    total_hours = sum(d["duration"] for d in data) / 3600
    print(f"   Total duration: {total_hours:.2f} hours")
    
    # Shuffle and split
    import random
    random.seed(42)
    random.shuffle(data)
    split_idx = int(len(data) * 0.9)
    train_data = data[:split_idx]
    val_data = data[split_idx:]
    print(f"   Train: {len(train_data)}, Validation: {len(val_data)}")
    
    # ============== STEP 2: BUILD VOCABULARY ==============
    print("\n[STEP 2] Building vocabulary from data...")
    
    # Get all unique characters from transcriptions
    all_text = " ".join([d["text"] for d in data])
    vocab_chars = sorted(list(set(all_text)))
    
    # Build vocab dict - CRITICAL: must match exactly what's in data
    vocab_dict = {char: idx for idx, char in enumerate(vocab_chars)}
    vocab_dict["|"] = vocab_dict.pop(" ")  # Word delimiter
    vocab_dict["[UNK]"] = len(vocab_dict)
    vocab_dict["[PAD]"] = len(vocab_dict)
    
    print(f"   Vocabulary size: {len(vocab_dict)}")
    print(f"   Characters: {list(vocab_dict.keys())}")
    
    # Save vocab
    vocab_path = OUTPUT_DIR / "vocab.json"
    with open(vocab_path, "w") as f:
        json.dump(vocab_dict, f)
    
    # ============== STEP 3: CREATE PROCESSOR ==============
    print("\n[STEP 3] Creating tokenizer and processor...")
    
    from transformers import (
        Wav2Vec2CTCTokenizer,
        Wav2Vec2FeatureExtractor, 
        Wav2Vec2Processor,
        Wav2Vec2ForCTC,
        TrainingArguments,
        Trainer
    )
    
    tokenizer = Wav2Vec2CTCTokenizer(
        str(vocab_path),
        unk_token="[UNK]",
        pad_token="[PAD]",
        word_delimiter_token="|"
    )
    
    feature_extractor = Wav2Vec2FeatureExtractor(
        feature_size=1,
        sampling_rate=SAMPLING_RATE,
        padding_value=0.0,
        do_normalize=True,
        return_attention_mask=True
    )
    
    processor = Wav2Vec2Processor(
        feature_extractor=feature_extractor,
        tokenizer=tokenizer
    )
    
    # Save processor
    processor.save_pretrained(str(OUTPUT_DIR))
    print(f"   Saved processor to {OUTPUT_DIR}")
    
    # ============== STEP 4: CREATE DATASET ==============
    print("\n[STEP 4] Creating datasets (loading audio with soundfile)...")
    
    from datasets import Dataset
    import librosa
    
    def load_and_prepare(data_list, name="dataset"):
        """Load audio files and prepare for training"""
        prepared = []
        for i, item in enumerate(data_list):
            if i % 200 == 0:
                print(f"   Processing {name}: {i}/{len(data_list)}")
            try:
                # Load audio with librosa (handles resampling)
                audio, sr = librosa.load(item["path"], sr=SAMPLING_RATE)
                
                # Process audio
                input_values = processor(audio, sampling_rate=SAMPLING_RATE).input_values[0]
                
                # Process text to labels
                labels = processor(text=item["text"]).input_ids
                
                prepared.append({
                    "input_values": input_values,
                    "labels": labels
                })
            except Exception as e:
                print(f"   Error loading {item['path']}: {e}")
                continue
        return prepared
    
    print("   Processing train dataset...")
    train_prepared = load_and_prepare(train_data, "train")
    print("   Processing validation dataset...")
    val_prepared = load_and_prepare(val_data, "val")
    
    # Create HuggingFace datasets from prepared data
    train_dataset = Dataset.from_dict({
        "input_values": [p["input_values"] for p in train_prepared],
        "labels": [p["labels"] for p in train_prepared]
    })
    val_dataset = Dataset.from_dict({
        "input_values": [p["input_values"] for p in val_prepared],
        "labels": [p["labels"] for p in val_prepared]
    })
    
    print(f"   Train samples: {len(train_dataset)}")
    print(f"   Val samples: {len(val_dataset)}")
    
    # ============== STEP 5: DATA COLLATOR ==============
    print("\n[STEP 5] Setting up data collator...")
    
    @dataclass
    class DataCollatorCTCWithPadding:
        processor: Wav2Vec2Processor
        padding: Union[bool, str] = True
        
        def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
            # Separate inputs and labels
            input_features = [{"input_values": f["input_values"]} for f in features]
            label_features = [{"input_ids": f["labels"]} for f in features]
            
            # Pad inputs
            batch = self.processor.pad(input_features, padding=self.padding, return_tensors="pt")
            
            # Pad labels - CRITICAL: use -100 for padding (ignored in loss)
            labels_batch = self.processor.pad(labels=label_features, padding=self.padding, return_tensors="pt")
            labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)
            batch["labels"] = labels
            
            return batch
    
    data_collator = DataCollatorCTCWithPadding(processor=processor)
    
    # ============== STEP 6: LOAD MODEL ==============
    print("\n[STEP 6] Loading pre-trained model...")
    
    # IMPORTANT: ignore_mismatched_sizes=True because we have different vocab
    model = Wav2Vec2ForCTC.from_pretrained(
        MODEL_NAME,
        ctc_loss_reduction="mean",
        pad_token_id=processor.tokenizer.pad_token_id,
        vocab_size=len(processor.tokenizer),
        ignore_mismatched_sizes=True  # Critical for custom vocab
    )
    
    # CRITICAL FIX: Freeze feature extractor to prevent blank collapse
    model.freeze_feature_extractor()
    print("   [?] FROZEN feature extractor (CNN layers)")
    print("   This is CRITICAL for small datasets to prevent WER 100%!")
    
    # ============== STEP 7: METRICS ==============
    print("\n[STEP 7] Setting up WER metric...")
    
    import evaluate
    wer_metric = evaluate.load("wer")
    
    def compute_metrics(pred):
        pred_logits = pred.predictions
        pred_ids = np.argmax(pred_logits, axis=-1)
        
        # Replace -100 with pad token for decoding
        pred.label_ids[pred.label_ids == -100] = processor.tokenizer.pad_token_id
        
        # Decode
        pred_str = processor.batch_decode(pred_ids)
        label_str = processor.batch_decode(pred.label_ids, group_tokens=False)
        
        # Debug: print first prediction
        if len(pred_str) > 0:
            print(f"\n   [DEBUG] Pred: '{pred_str[0][:50]}...' | Label: '{label_str[0][:50]}...'")
        
        wer = wer_metric.compute(predictions=pred_str, references=label_str)
        return {"wer": wer}
    
    # ============== STEP 8: TRAINING ==============
    print("\n[STEP 8] Configuring training...")
    
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        group_by_length=True,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        eval_strategy="steps",
        eval_steps=100,
        save_steps=200,
        logging_steps=25,
        learning_rate=LEARNING_RATE,
        warmup_steps=WARMUP_STEPS,
        num_train_epochs=EPOCHS,
        fp16=torch.cuda.is_available(),
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        dataloader_num_workers=0,
        report_to="none",
        # Additional stability settings
        max_grad_norm=1.0,
        weight_decay=0.005,
    )
    
    trainer = Trainer(
        model=model,
        data_collator=data_collator,
        args=training_args,
        compute_metrics=compute_metrics,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=processor.feature_extractor,
    )
    
    print("\n" + "="*70)
    print("STARTING TRAINING")
    print("="*70)
    print(f"Model: {MODEL_NAME}")
    print(f"Train samples: {len(train_dataset)}")
    print(f"Val samples: {len(val_dataset)}")
    print(f"Learning rate: {LEARNING_RATE} (LOW to prevent blank collapse)")
    print(f"Epochs: {EPOCHS}")
    print(f"Batch size: {BATCH_SIZE} x {GRAD_ACCUM} = {BATCH_SIZE * GRAD_ACCUM}")
    print(f"Warmup steps: {WARMUP_STEPS}")
    print(f"Feature extractor: FROZEN")
    print("="*70 + "\n")
    
    # Train
    trainer.train()
    
    # ============== STEP 9: SAVE & EVALUATE ==============
    print("\n" + "="*70)
    print("SAVING FINAL MODEL")
    print("="*70)
    
    final_path = OUTPUT_DIR / "final_model"
    os.makedirs(final_path, exist_ok=True)
    trainer.save_model(str(final_path))
    processor.save_pretrained(str(final_path))
    print(f"Saved to: {final_path}")
    
    # Final evaluation
    print("\n[FINAL EVALUATION]")
    results = trainer.evaluate()
    final_wer = results['eval_wer'] * 100
    print(f"Final WER: {final_wer:.2f}%")
    
    if final_wer < 50:
        print("\n[OK] SUCCESS! WER is below 50% - model is learning!")
    elif final_wer < 100:
        print("\n[WARN] PARTIAL SUCCESS - WER decreased but needs more training")
    else:
        print("\n[X] WER still at 100% - check data/labels")
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE!")
    print("="*70)
