#!/usr/bin/env python3
"""
Monica AI — Whisper Fine-Tuning Script
=======================================
Fine-tunes OpenAI Whisper on downloaded speech datasets for improved
transcription accuracy. Uses LoRA (Low-Rank Adaptation) to fit within
RTX 4060 8GB VRAM.

Prerequisites:
  1. Run download_whisper_datasets.py first to get training data
  2. Requires: transformers, datasets, peft, accelerate, evaluate, jiwer

Usage:
  python scripts/finetune_whisper.py
  python scripts/finetune_whisper.py --model openai/whisper-small
  python scripts/finetune_whisper.py --epochs 3 --batch-size 4
  python scripts/finetune_whisper.py --resume  (resume from checkpoint)

Output:
  models/whisper_finetuned/  (fine-tuned model)
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("WhisperFinetune")

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATASET_DIR = PROJECT_ROOT / "data" / "datasets" / "whisper_finetune"
OUTPUT_DIR = PROJECT_ROOT / "models" / "whisper_finetuned"


def load_manifest_dataset(manifest_path: Path):
    """Load a manifest JSON into a HuggingFace Dataset."""
    import numpy as np
    import soundfile as sf
    from datasets import Dataset, Audio

    with open(manifest_path, 'r') as f:
        entries = json.load(f)

    base_dir = manifest_path.parent
    # For combined manifest, base_dir is the whisper_finetune dir
    # For individual manifests, base_dir is the dataset subdir

    audio_paths = []
    texts = []
    for entry in entries:
        audio_file = base_dir / entry["audio_path"]
        if audio_file.exists():
            audio_paths.append(str(audio_file))
            texts.append(entry["text"])

    logger.info(f"Loaded {len(audio_paths):,} valid samples from {manifest_path.name}")

    ds = Dataset.from_dict({
        "audio": audio_paths,
        "text": texts,
    })
    ds = ds.cast_column("audio", Audio(sampling_rate=16000))
    return ds


def prepare_dataset(batch, processor):
    """Prepare a batch for Whisper training."""
    audio = batch["audio"]

    # Compute input features from audio
    batch["input_features"] = processor.feature_extractor(
        audio["array"], sampling_rate=audio["sampling_rate"]
    ).input_features[0]

    # Encode target text
    batch["labels"] = processor.tokenizer(batch["text"]).input_ids
    return batch


def compute_metrics(pred, tokenizer, metric):
    """Compute WER metric."""
    pred_ids = pred.predictions
    label_ids = pred.label_ids

    # Replace -100 with pad token id
    label_ids[label_ids == -100] = tokenizer.pad_token_id

    pred_str = tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
    label_str = tokenizer.batch_decode(label_ids, skip_special_tokens=True)

    wer = 100 * metric.compute(predictions=pred_str, references=label_str)
    return {"wer": wer}


def main():
    parser = argparse.ArgumentParser(description="Fine-tune Whisper for Monica AI")
    parser.add_argument("--model", type=str, default="openai/whisper-small",
                       help="Base Whisper model (default: whisper-small)")
    parser.add_argument("--epochs", type=int, default=3,
                       help="Training epochs (default: 3)")
    parser.add_argument("--batch-size", type=int, default=4,
                       help="Per-device batch size (default: 4, reduce if OOM)")
    parser.add_argument("--lr", type=float, default=1e-5,
                       help="Learning rate (default: 1e-5)")
    parser.add_argument("--lora-rank", type=int, default=32,
                       help="LoRA rank (default: 32, higher = more capacity)")
    parser.add_argument("--max-train-samples", type=int, default=0,
                       help="Max training samples (0 = all)")
    parser.add_argument("--max-eval-samples", type=int, default=2000,
                       help="Max evaluation samples (default: 2000)")
    parser.add_argument("--resume", action="store_true",
                       help="Resume from last checkpoint")
    parser.add_argument("--no-lora", action="store_true",
                       help="Full fine-tuning instead of LoRA (needs more VRAM)")
    parser.add_argument("--manifest", type=str, default="",
                       help="Path to specific manifest (default: combined)")
    args = parser.parse_args()

    import torch
    from transformers import (
        WhisperForConditionalGeneration,
        WhisperProcessor,
        Seq2SeqTrainingArguments,
        Seq2SeqTrainer,
    )
    from transformers.models.whisper.english_normalizer import BasicTextNormalizer
    import evaluate
    from functools import partial

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Device: {device}")
    if device == "cuda":
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        logger.info(f"VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")

    # 1. Load manifest
    if args.manifest:
        manifest_path = Path(args.manifest)
    else:
        manifest_path = DATASET_DIR / "combined_manifest.json"
        if not manifest_path.exists():
            # Try individual manifests
            for subdir in DATASET_DIR.iterdir():
                if (subdir / "manifest.json").exists():
                    manifest_path = subdir / "manifest.json"
                    break

    if not manifest_path.exists():
        logger.error(f"No manifest found at {manifest_path}")
        logger.error("Run download_whisper_datasets.py first!")
        return

    logger.info(f"Loading dataset from: {manifest_path}")
    full_ds = load_manifest_dataset(manifest_path)

    # 2. Split into train/eval
    split = full_ds.train_test_split(test_size=min(args.max_eval_samples, len(full_ds) // 10))
    train_ds = split["train"]
    eval_ds = split["test"]

    if args.max_train_samples > 0:
        train_ds = train_ds.select(range(min(args.max_train_samples, len(train_ds))))

    logger.info(f"Train: {len(train_ds):,} samples, Eval: {len(eval_ds):,} samples")

    # 3. Load processor and model
    logger.info(f"Loading model: {args.model}")
    processor = WhisperProcessor.from_pretrained(args.model, language="english", task="transcribe")
    model = WhisperForConditionalGeneration.from_pretrained(args.model)
    model.generation_config.language = "english"
    model.generation_config.task = "transcribe"
    model.generation_config.forced_decoder_ids = None

    # 4. Apply LoRA if requested (saves VRAM)
    if not args.no_lora:
        from peft import LoraConfig, get_peft_model, TaskType

        lora_config = LoraConfig(
            r=args.lora_rank,
            lora_alpha=64,
            target_modules=["q_proj", "v_proj", "k_proj", "out_proj", "fc1", "fc2"],
            lora_dropout=0.05,
            bias="none",
            task_type=TaskType.SEQ_2_SEQ_LM,
        )
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()
        logger.info(f"LoRA applied (rank={args.lora_rank})")

    # 5. Preprocess datasets
    logger.info("Preprocessing training data...")
    train_ds = train_ds.map(
        partial(prepare_dataset, processor=processor),
        remove_columns=train_ds.column_names,
        num_proc=1,
    )

    logger.info("Preprocessing evaluation data...")
    eval_ds = eval_ds.map(
        partial(prepare_dataset, processor=processor),
        remove_columns=eval_ds.column_names,
        num_proc=1,
    )

    # 6. Data collator
    from dataclasses import dataclass
    from typing import Any, Dict, List, Union

    @dataclass
    class DataCollatorSpeechSeq2SeqWithPadding:
        processor: Any
        decoder_start_token_id: int

        def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
            input_features = [{"input_features": f["input_features"]} for f in features]
            batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")

            label_features = [{"input_ids": f["labels"]} for f in features]
            labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")

            labels = labels_batch["input_ids"].masked_fill(
                labels_batch.attention_mask.ne(1), -100
            )
            if (labels[:, 0] == self.decoder_start_token_id).all().cpu().item():
                labels = labels[:, 1:]

            batch["labels"] = labels
            return batch

    data_collator = DataCollatorSpeechSeq2SeqWithPadding(
        processor=processor,
        decoder_start_token_id=model.config.decoder_start_token_id,
    )

    # 7. Metrics
    metric = evaluate.load("wer")
    normalizer = BasicTextNormalizer()

    def compute_metrics_fn(pred):
        pred_ids = pred.predictions
        label_ids = pred.label_ids
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
        pred_str = processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)
        # Normalize
        pred_str = [normalizer(t) for t in pred_str]
        label_str = [normalizer(t) for t in label_str]
        wer = 100 * metric.compute(predictions=pred_str, references=label_str)
        return {"wer": wer}

    # 8. Training arguments
    output_dir = str(OUTPUT_DIR)
    training_args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=4,  # Effective batch = batch_size * 4
        learning_rate=args.lr,
        warmup_steps=500,
        num_train_epochs=args.epochs,
        gradient_checkpointing=True,
        fp16=torch.cuda.is_available(),
        eval_strategy="steps",
        eval_steps=1000,
        save_strategy="steps",
        save_steps=1000,
        save_total_limit=3,
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        logging_steps=100,
        predict_with_generate=True,
        generation_max_length=225,
        report_to="none",
        push_to_hub=False,
        dataloader_num_workers=2,
        remove_unused_columns=False,
    )

    # 9. Trainer
    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=data_collator,
        compute_metrics=compute_metrics_fn,
        processing_class=processor.feature_extractor,
    )

    # 10. Train!
    logger.info("="*60)
    logger.info("Starting Whisper fine-tuning")
    logger.info(f"Model: {args.model}")
    logger.info(f"LoRA: {'No' if args.no_lora else f'Yes (rank={args.lora_rank})'}")
    logger.info(f"Epochs: {args.epochs}")
    logger.info(f"Batch size: {args.batch_size} (effective: {args.batch_size * 4})")
    logger.info(f"Learning rate: {args.lr}")
    logger.info(f"Output: {output_dir}")
    logger.info("="*60)

    resume_from = None
    if args.resume:
        checkpoints = list(Path(output_dir).glob("checkpoint-*"))
        if checkpoints:
            resume_from = str(sorted(checkpoints, key=lambda x: int(x.name.split("-")[1]))[-1])
            logger.info(f"Resuming from: {resume_from}")

    trainer.train(resume_from_checkpoint=resume_from)

    # 11. Save final model
    final_dir = str(OUTPUT_DIR / "final")
    trainer.save_model(final_dir)
    processor.save_pretrained(final_dir)
    logger.info(f"Fine-tuned model saved to: {final_dir}")
    logger.info("Done! Update stt_service.py to use this model.")


if __name__ == "__main__":
    main()
