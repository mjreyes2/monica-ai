"""
FINAL WORKING Wav2Vec2 Fine-tuning Script
KEY FIX: Use the pretrained model's EXISTING processor/vocabulary
DO NOT create custom vocabulary - that breaks the decoder!

Based on HuggingFace official tutorial.
"""

if __name__ == "__main__":
    import os
    import re
    import torch
    import numpy as np
    import librosa
    from dataclasses import dataclass
    from typing import Any, Dict, List, Union
    from pathlib import Path
    
    print("="*70)
    print("WAV2VEC2 FINE-TUNING - USING PRETRAINED VOCABULARY")
    print("="*70)
    
    # ============== CONFIGURATION ==============
    PROJECT_DIR = Path("C:/Monica")
    RECORDINGS_DIR = PROJECT_DIR / "data" / "training" / "voice_training" / "recordings" / "MJP"
    OUTPUT_DIR = PROJECT_DIR / "models" / "wav2vec2_final"
    
    # Use pretrained model WITH its processor (critical fix!)
    MODEL_NAME = "facebook/wav2vec2-base-960h"
    SAMPLING_RATE = 16000
    
    # Training params - conservative for stability
    LEARNING_RATE = 1e-5  # Very low
    EPOCHS = 10
    BATCH_SIZE = 4
    GRAD_ACCUM = 2
    WARMUP_STEPS = 100
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # ============== STEP 1: LOAD PRETRAINED PROCESSOR ==============
    print("\n[STEP 1] Loading PRETRAINED processor (keeps working vocabulary)...")
    
    from transformers import (
        Wav2Vec2Processor,
        Wav2Vec2ForCTC,
        TrainingArguments,
        Trainer
    )
    
    # CRITICAL: Load the pretrained processor - DO NOT create custom vocab!
    processor = Wav2Vec2Processor.from_pretrained(MODEL_NAME)
    print(f"   Loaded processor with vocab size: {len(processor.tokenizer)}")
    print(f"   Vocab sample: {list(processor.tokenizer.get_vocab().keys())[:10]}")
    
    # ============== STEP 2: LOAD AND PREPARE DATA ==============
    print("\n[STEP 2] Loading recordings...")
    
    def clean_text(text):
        """Clean text to match pretrained vocab (uppercase letters + space)"""
        text = text.upper()  # Pretrained model uses UPPERCASE
        text = text.replace("'", "").replace("'", "")
        text = re.sub(r'[^A-Z ]', '', text)
        text = re.sub(r' +', ' ', text)
        return text.strip()
    
    def extract_text_from_filename(filename):
        """Extract transcription from filename"""
        name = Path(filename).stem
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
    
    import soundfile as sf
    wav_files = list(RECORDINGS_DIR.glob("*.wav"))
    print(f"   Found {len(wav_files)} WAV files")
    
    data = []
    for wav_file in wav_files:
        text = extract_text_from_filename(wav_file.name)
        if text and len(text) >= 2:
            try:
                info = sf.info(str(wav_file))
                if 0.5 <= info.duration <= 20:
                    data.append({"path": str(wav_file), "text": text, "duration": info.duration})
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
    
    # ============== STEP 3: PREPARE DATASETS ==============
    print("\n[STEP 3] Preparing datasets...")
    
    from datasets import Dataset
    
    def load_and_prepare(data_list, name="dataset"):
        prepared = []
        for i, item in enumerate(data_list):
            if i % 500 == 0:
                print(f"   {name}: {i}/{len(data_list)}")
            try:
                audio, sr = librosa.load(item["path"], sr=SAMPLING_RATE)
                input_values = processor(audio, sampling_rate=SAMPLING_RATE).input_values[0]
                
                # Tokenize text directly with tokenizer
                labels = processor.tokenizer(item["text"]).input_ids
                
                if len(labels) > 0:
                    prepared.append({"input_values": input_values, "labels": labels})
            except Exception as e:
                print(f"   Error: {e}")
        return prepared
    
    train_prepared = load_and_prepare(train_data, "train")
    val_prepared = load_and_prepare(val_data, "val")
    
    train_dataset = Dataset.from_dict({
        "input_values": [p["input_values"] for p in train_prepared],
        "labels": [p["labels"] for p in train_prepared]
    })
    val_dataset = Dataset.from_dict({
        "input_values": [p["input_values"] for p in val_prepared],
        "labels": [p["labels"] for p in val_prepared]
    })
    
    print(f"   Train: {len(train_dataset)}, Val: {len(val_dataset)}")
    
    # ============== STEP 4: DATA COLLATOR ==============
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
    
    # ============== STEP 5: LOAD MODEL ==============
    print("\n[STEP 4] Loading model...")
    
    model = Wav2Vec2ForCTC.from_pretrained(MODEL_NAME)
    model.freeze_feature_extractor()
    print("   [?] Loaded model with ORIGINAL vocabulary")
    print("   [?] Frozen feature extractor")
    
    # ============== STEP 6: METRICS ==============
    import evaluate
    wer_metric = evaluate.load("wer")
    
    def compute_metrics(pred):
        pred_logits = pred.predictions
        pred_ids = np.argmax(pred_logits, axis=-1)
        pred.label_ids[pred.label_ids == -100] = processor.tokenizer.pad_token_id
        
        pred_str = processor.batch_decode(pred_ids)
        label_str = processor.batch_decode(pred.label_ids, group_tokens=False)
        
        # Debug output
        if len(pred_str) > 0 and len(label_str) > 0:
            print(f"\n   [SAMPLE] Pred: '{pred_str[0][:40]}' | Label: '{label_str[0][:40]}'")
        
        wer = wer_metric.compute(predictions=pred_str, references=label_str)
        return {"wer": wer}
    
    # ============== STEP 7: TRAINING ==============
    print("\n[STEP 5] Starting training...")
    
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        group_by_length=True,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        eval_strategy="steps",
        eval_steps=50,
        save_steps=100,
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
        max_grad_norm=1.0,
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
    
    print(f"\n{'='*70}")
    print(f"Training: {len(train_dataset)} samples, {EPOCHS} epochs")
    print(f"Learning rate: {LEARNING_RATE}")
    print(f"Using PRETRAINED vocabulary (critical fix!)")
    print(f"{'='*70}\n")
    
    trainer.train()
    
    # Save
    print("\n[SAVING]")
    final_path = OUTPUT_DIR / "final_model"
    os.makedirs(final_path, exist_ok=True)
    trainer.save_model(str(final_path))
    processor.save_pretrained(str(final_path))
    
    results = trainer.evaluate()
    print(f"\n{'='*70}")
    print(f"FINAL WER: {results['eval_wer']*100:.2f}%")
    print(f"{'='*70}")
