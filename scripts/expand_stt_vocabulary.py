#!/usr/bin/env python3
"""
STT Vocabulary Expansion Training
==================================
This script helps you:
1. Record phrases with expanded vocabulary
2. Fine-tune your wav2vec2 model on your voice
3. Improve recognition of specific words

Run this script to start recording new training phrases.
"""

import os
import sys
import json
import time
import wave
import threading
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent
RECORDINGS_DIR = PROJECT_ROOT / "stt_vocabulary_training" / "recordings"
MODEL_DIR = PROJECT_ROOT / "models" / "wav2vec2_final" / "final_model"
OUTPUT_DIR = PROJECT_ROOT / "models" / "wav2vec2_expanded"

# Create directories
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Expanded vocabulary phrases - words that are commonly misrecognized
TRAINING_PHRASES = [
    # Psychology and mental health
    "what is psychology",
    "tell me about clinical psychology",
    "explain psychological therapy",
    "what is counseling",
    "describe cognitive behavioral therapy",
    "what is psychotherapy",
    "explain mental health",
    "what is psychiatry",
    "tell me about anxiety",
    "what is depression",
    
    # Monica-specific
    "monica initialize",
    "hey monica",
    "monica help me",
    "monica what time is it",
    "monica set a reminder",
    "monica play some music",
    "monica turn off the lights",
    "monica what is the weather",
    "monica tell me a joke",
    "monica search for",
    
    # Common questions
    "what is today's date",
    "what time is it",
    "what is the weather like",
    "tell me about yourself",
    "who created you",
    "what can you do",
    "help me with something",
    "I have a question",
    "can you explain",
    "what does that mean",
    
    # Technical terms
    "artificial intelligence",
    "machine learning",
    "neural network",
    "deep learning",
    "natural language processing",
    "computer vision",
    "speech recognition",
    "text to speech",
    "voice assistant",
    "smart home",
    
    # Historical figures
    "christopher columbus",
    "who discovered america",
    "tell me about history",
    "when was the renaissance",
    "who was shakespeare",
    
    # Numbers and dates
    "one two three four five",
    "six seven eight nine ten",
    "january february march",
    "april may june july",
    "august september october",
    "november december",
    "monday tuesday wednesday",
    "thursday friday saturday sunday",
    
    # Common words that get misrecognized
    "initialize the system",
    "activate voice control",
    "deactivate the alarm",
    "schedule a meeting",
    "remind me tomorrow",
    "what is the temperature",
    "convert celsius to fahrenheit",
    "calculate the percentage",
    "summarize this article",
    "translate to spanish",
    
    # Longer sentences for context
    "I would like to know more about psychology and mental health",
    "can you tell me what the weather will be like tomorrow",
    "please set a reminder for my meeting at three o'clock",
    "I need help understanding this concept",
    "what are the symptoms of anxiety and depression",
    "how does artificial intelligence work",
    "explain the difference between machine learning and deep learning",
    "who was the first person to walk on the moon",
    "what is the capital of the united states",
    "how many countries are there in the world",
]


def record_audio(filename, duration=5, sample_rate=16000):
    """Record audio from microphone."""
    try:
        import pyaudio
    except ImportError:
        print("ERROR: pyaudio not installed. Run: pip install pyaudio")
        return False
    
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    
    p = pyaudio.PyAudio()
    
    # Find input device
    device_index = None
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            device_index = i
            break
    
    if device_index is None:
        print("ERROR: No input device found")
        return False
    
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=sample_rate,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=CHUNK
    )
    
    print(f"Recording for {duration} seconds...")
    frames = []
    
    for i in range(0, int(sample_rate / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)
    
    print("Recording complete!")
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Save to WAV file
    wf = wave.open(str(filename), 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(sample_rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    return True


def record_training_phrases():
    """Interactive recording session for training phrases."""
    print("=" * 70)
    print("STT VOCABULARY EXPANSION - RECORDING SESSION")
    print("=" * 70)
    print()
    print(f"You will record {len(TRAINING_PHRASES)} phrases.")
    print("Each phrase will be recorded for 5 seconds.")
    print("Speak clearly and naturally.")
    print()
    print("Press ENTER to start, or 'q' to quit at any time.")
    print("=" * 70)
    
    # Load progress
    progress_file = RECORDINGS_DIR / "progress.json"
    recorded = []
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            recorded = json.load(f)
        print(f"\nResuming from phrase {len(recorded) + 1}/{len(TRAINING_PHRASES)}")
    
    input("\nPress ENTER to begin...")
    
    for i, phrase in enumerate(TRAINING_PHRASES):
        if i < len(recorded):
            continue  # Skip already recorded
        
        print()
        print(f"[{i+1}/{len(TRAINING_PHRASES)}]")
        print(f"Say: \"{phrase}\"")
        print()
        
        user_input = input("Press ENTER to record, 's' to skip, 'q' to quit: ").strip().lower()
        
        if user_input == 'q':
            print("Saving progress and exiting...")
            break
        elif user_input == 's':
            print("Skipped.")
            continue
        
        # Record
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_phrase = phrase.replace(" ", "_").replace("'", "")[:50]
        filename = RECORDINGS_DIR / f"phrase_{i:04d}_{timestamp}_{safe_phrase}.wav"
        
        print()
        print(">>> GET READY <<<")
        time.sleep(1)
        print(">>> RECORDING NOW <<<")
        
        success = record_audio(filename, duration=5)
        
        if success:
            recorded.append({
                "index": i,
                "phrase": phrase,
                "filename": str(filename),
                "timestamp": timestamp
            })
            
            # Save progress
            with open(progress_file, 'w') as f:
                json.dump(recorded, f, indent=2)
            
            print(f" Saved: {filename.name}")
        else:
            print(" Recording failed, try again")
    
    print()
    print("=" * 70)
    print(f"Recording session complete! {len(recorded)} phrases recorded.")
    print(f"Recordings saved to: {RECORDINGS_DIR}")
    print("=" * 70)
    
    return recorded


def create_training_manifest():
    """Create training manifest from recorded phrases."""
    print("\nCreating training manifest...")
    
    progress_file = RECORDINGS_DIR / "progress.json"
    if not progress_file.exists():
        print("No recordings found. Run recording session first.")
        return None
    
    with open(progress_file, 'r') as f:
        recorded = json.load(f)
    
    manifest = []
    for entry in recorded:
        wav_path = Path(entry['filename'])
        if wav_path.exists():
            manifest.append({
                "audio_filepath": str(wav_path),
                "text": entry['phrase'].upper(),  # wav2vec2 uses uppercase
                "duration": 5.0
            })
    
    manifest_file = RECORDINGS_DIR / "training_manifest.json"
    with open(manifest_file, 'w') as f:
        for entry in manifest:
            f.write(json.dumps(entry) + "\n")
    
    print(f"Created manifest with {len(manifest)} entries: {manifest_file}")
    return manifest_file


def finetune_model():
    """Fine-tune the wav2vec2 model on new recordings."""
    print("\n" + "=" * 70)
    print("FINE-TUNING MODEL ON NEW VOCABULARY")
    print("=" * 70)
    
    manifest_file = create_training_manifest()
    if manifest_file is None:
        return
    
    # Check if we have enough data
    with open(manifest_file, 'r') as f:
        entries = [json.loads(line) for line in f]
    
    if len(entries) < 10:
        print(f"Only {len(entries)} recordings. Record at least 10 phrases for effective training.")
        return
    
    print(f"\nTraining on {len(entries)} recordings...")
    print(f"Base model: {MODEL_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    
    # Import training dependencies
    import torch
    import numpy as np
    import librosa
    from dataclasses import dataclass
    from typing import Union
    from transformers import (
        Wav2Vec2Processor,
        Wav2Vec2ForCTC,
        TrainingArguments,
        Trainer
    )
    from datasets import Dataset
    
    # Load processor and model
    print("\nLoading model...")
    processor = Wav2Vec2Processor.from_pretrained(str(MODEL_DIR))
    model = Wav2Vec2ForCTC.from_pretrained(str(MODEL_DIR))
    model.freeze_feature_extractor()
    
    # Prepare data
    print("Preparing data...")
    
    def load_audio(filepath):
        audio, sr = librosa.load(filepath, sr=16000)
        return audio
    
    prepared = []
    for entry in entries:
        try:
            audio = load_audio(entry['audio_filepath'])
            input_values = processor(audio, sampling_rate=16000).input_values[0]
            labels = processor.tokenizer(entry['text']).input_ids
            if len(labels) > 0:
                prepared.append({"input_values": input_values, "labels": labels})
        except Exception as e:
            print(f"Error processing {entry['audio_filepath']}: {e}")
    
    if len(prepared) < 5:
        print("Not enough valid recordings for training.")
        return
    
    # Split into train/val
    split_idx = max(1, int(len(prepared) * 0.9))
    train_data = prepared[:split_idx]
    val_data = prepared[split_idx:] if split_idx < len(prepared) else prepared[-1:]
    
    train_dataset = Dataset.from_dict({
        "input_values": [p["input_values"] for p in train_data],
        "labels": [p["labels"] for p in train_data]
    })
    val_dataset = Dataset.from_dict({
        "input_values": [p["input_values"] for p in val_data],
        "labels": [p["labels"] for p in val_data]
    })
    
    print(f"Train: {len(train_dataset)}, Val: {len(val_dataset)}")
    
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
    
    # Training arguments - conservative for fine-tuning
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        group_by_length=True,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=4,
        eval_strategy="steps",
        eval_steps=20,
        save_steps=50,
        logging_steps=10,
        learning_rate=5e-6,  # Very low for fine-tuning
        warmup_steps=50,
        num_train_epochs=5,
        fp16=torch.cuda.is_available(),
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        dataloader_num_workers=0,
        report_to="none",
        max_grad_norm=1.0,
    )
    
    # Metrics
    import evaluate
    wer_metric = evaluate.load("wer")
    
    def compute_metrics(pred):
        pred_logits = pred.predictions
        pred_ids = np.argmax(pred_logits, axis=-1)
        pred.label_ids[pred.label_ids == -100] = processor.tokenizer.pad_token_id
        
        pred_str = processor.batch_decode(pred_ids)
        label_str = processor.batch_decode(pred.label_ids, group_tokens=False)
        
        wer = wer_metric.compute(predictions=pred_str, references=label_str)
        return {"wer": wer}
    
    # Train
    trainer = Trainer(
        model=model,
        data_collator=data_collator,
        args=training_args,
        compute_metrics=compute_metrics,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=processor.feature_extractor,
    )
    
    print("\n" + "=" * 70)
    print("STARTING TRAINING")
    print("=" * 70)
    
    trainer.train()
    
    # Save
    final_path = OUTPUT_DIR / "final_model"
    final_path.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(final_path))
    processor.save_pretrained(str(final_path))
    
    results = trainer.evaluate()
    
    print("\n" + "=" * 70)
    print(f"TRAINING COMPLETE!")
    print(f"Final WER: {results['eval_wer']*100:.2f}%")
    print(f"Model saved to: {final_path}")
    print("=" * 70)
    print("\nTo use the new model, update speechbrain_final.py to point to:")
    print(f"  {final_path}")


def main():
    print()
    print("=" * 70)
    print("STT VOCABULARY EXPANSION TOOL")
    print("=" * 70)
    print()
    print("Options:")
    print("  1. Record training phrases (interactive)")
    print("  2. Fine-tune model on recordings")
    print("  3. Both (record then train)")
    print("  q. Quit")
    print()
    
    choice = input("Enter choice (1/2/3/q): ").strip().lower()
    
    if choice == '1':
        record_training_phrases()
    elif choice == '2':
        finetune_model()
    elif choice == '3':
        recorded = record_training_phrases()
        if recorded and len(recorded) >= 10:
            finetune_model()
        else:
            print("\nNeed at least 10 recordings to train. Record more phrases first.")
    elif choice == 'q':
        print("Goodbye!")
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()
