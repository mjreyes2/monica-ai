"""
Prepare ALL training data by combining:
1. Monica GUI recordings (recordings/wake_phrases/)
2. New phrase recordings (recordings/training_phrases/)

Creates dataset for HuggingFace Transformers fine-tuning (fixes SpeechBrain CTCTextEncoder bug)
"""

import os
import json
import re
import soundfile as sf
import random
from pathlib import Path

try:
    from datasets import Dataset, DatasetDict, Audio
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False

# Paths - current project layout under data/training
PROJECT_DIR = Path("C:/Monica")
GUI_RECORDINGS_DIR = PROJECT_DIR / "data" / "training" / "recordings" / "wake_phrases"
PHRASE_RECORDINGS_DIR = PROJECT_DIR / "data" / "training" / "recordings" / "training_phrases"
PHRASES_FILE = PROJECT_DIR / "data" / "training" / "PHRASES_MASTER.txt"
OUTPUT_DIR = PROJECT_DIR / "data" / "training" / "datasets" / "stt_combined"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_transcription(text):
    """Clean transcription to only contain a-z and space."""
    text = text.lower()
    text = text.replace("'", "").replace("'", "")
    text = re.sub(r'[^a-z ]', '', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()

def get_audio_duration(filepath):
    """Get duration of audio file in seconds."""
    try:
        info = sf.info(filepath)
        return info.duration
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def extract_transcription_from_gui_filename(filename):
    """Extract transcription from Monica GUI filename like 'phrase_0004_20251209_231418_Monica_wake_up.wav'"""
    name = Path(filename).stem
    # Supported formats:
    # 1) phrase_0004_20251209_231418_Monica_wake_up
    # 2) phrase_00001_monica_initialize
    parts = name.split("_")

    # Format with timestamp
    if len(parts) >= 5 and parts[0] == "phrase" and parts[2].isdigit() and parts[3].isdigit():
        text_parts = parts[4:]
        return clean_transcription(" ".join(text_parts))

    # Simple indexed format without timestamp
    if len(parts) >= 3 and parts[0] == "phrase" and parts[1].isdigit():
        text_parts = parts[2:]
        return clean_transcription(" ".join(text_parts))

    return clean_transcription(name)

def extract_transcription_from_phrase_filename(filename, phrases):
    """Extract transcription from phrase filename like '0001_The_quick_brown_fox.wav'"""
    name = Path(filename).stem
    parts = name.split("_", 1)
    try:
        phrase_num = int(parts[0]) - 1  # 0-indexed
        if 0 <= phrase_num < len(phrases):
            return clean_transcription(phrases[phrase_num])
    except (ValueError, IndexError):
        pass
    
    if len(parts) > 1:
        text = parts[1].replace("_", " ")
        return clean_transcription(text)
    return clean_transcription(name)

def load_gui_recordings():
    """Load Monica GUI recordings."""
    data = []
    print(f"\nScanning GUI recordings from {GUI_RECORDINGS_DIR}")
    
    if not GUI_RECORDINGS_DIR.exists():
        print(f"  Directory not found!")
        return data
    
    wav_files = list(GUI_RECORDINGS_DIR.glob("*.wav"))
    print(f"  Found {len(wav_files)} files")
    
    for wav_file in wav_files:
        transcription = extract_transcription_from_gui_filename(wav_file.name)
        if not transcription or len(transcription) < 2:
            continue
            
        duration = get_audio_duration(str(wav_file))
        if duration is None or duration < 0.3 or duration > 30:
            continue
        
        data.append({
            "audio": str(wav_file.absolute()),
            "text": transcription,
            "duration": duration
        })
    
    print(f"  Loaded {len(data)} valid recordings")
    return data

def load_phrase_recordings():
    """Load new phrase recordings."""
    data = []
    print(f"\nScanning phrase recordings from {PHRASE_RECORDINGS_DIR}")
    
    # Load phrases for lookup
    phrases = []
    if PHRASES_FILE.exists():
        with open(PHRASES_FILE, "r", encoding="utf-8") as f:
            phrases = [line.strip() for line in f if line.strip()]
    
    if not PHRASE_RECORDINGS_DIR.exists():
        print(f"  Directory not found!")
        return data
    
    wav_files = list(PHRASE_RECORDINGS_DIR.glob("*.wav"))
    print(f"  Found {len(wav_files)} files")
    
    for wav_file in wav_files:
        transcription = extract_transcription_from_phrase_filename(wav_file.name, phrases)
        if not transcription or len(transcription) < 2:
            continue
            
        duration = get_audio_duration(str(wav_file))
        if duration is None or duration < 0.3 or duration > 30:
            continue
        
        data.append({
            "audio": str(wav_file.absolute()),
            "text": transcription,
            "duration": duration
        })
    
    print(f"  Loaded {len(data)} valid recordings")
    return data

def main():
    print("="*60)
    print("PREPARING COMBINED TRAINING DATA")
    print("="*60)
    
    # Load all data
    gui_data = load_gui_recordings()
    phrase_data = load_phrase_recordings()
    
    # Combine
    all_data = gui_data + phrase_data
    print(f"\n{'='*60}")
    print(f"TOTAL RECORDINGS: {len(all_data)}")
    print(f"  - GUI recordings: {len(gui_data)}")
    print(f"  - Phrase recordings: {len(phrase_data)}")
    
    total_duration = sum(d["duration"] for d in all_data)
    print(f"  - Total duration: {total_duration/60:.1f} minutes ({total_duration/3600:.2f} hours)")
    
    # Shuffle and split (90% train, 10% validation)
    random.seed(42)
    random.shuffle(all_data)
    
    split_idx = int(len(all_data) * 0.9)
    train_data = all_data[:split_idx]
    val_data = all_data[split_idx:]
    
    print(f"\nSplit:")
    print(f"  - Train: {len(train_data)} recordings")
    print(f"  - Validation: {len(val_data)} recordings")
    
    # Save as JSON for HuggingFace
    train_json = OUTPUT_DIR / "train.json"
    val_json = OUTPUT_DIR / "val.json"
    
    with open(train_json, "w", encoding="utf-8") as f:
        for item in train_data:
            json.dump(item, f)
            f.write("\n")
    
    with open(val_json, "w", encoding="utf-8") as f:
        for item in val_data:
            json.dump(item, f)
            f.write("\n")
    
    print(f"\nSaved:")
    print(f"  - {train_json}")
    print(f"  - {val_json}")
    
    # Optionally create HuggingFace Dataset if dependency is available.
    if HAS_DATASETS:
        print("\nCreating HuggingFace Dataset...")

        train_dataset = Dataset.from_dict({
            "audio": [d["audio"] for d in train_data],
            "text": [d["text"] for d in train_data]
        })
        val_dataset = Dataset.from_dict({
            "audio": [d["audio"] for d in val_data],
            "text": [d["text"] for d in val_data]
        })

        # Cast audio column
        train_dataset = train_dataset.cast_column("audio", Audio(sampling_rate=16000))
        val_dataset = val_dataset.cast_column("audio", Audio(sampling_rate=16000))

        dataset = DatasetDict({
            "train": train_dataset,
            "validation": val_dataset
        })

        dataset_path = OUTPUT_DIR / "dataset"
        dataset.save_to_disk(str(dataset_path))
        print(f"  - Saved HuggingFace dataset to {dataset_path}")
    else:
        print("\nSkipping HuggingFace dataset export (install 'datasets' to enable).")
    
    print("\n" + "="*60)
    print("DATA PREPARATION COMPLETE!")
    print("="*60)
    
    # Show sample transcriptions
    print("\nSample transcriptions:")
    for i, item in enumerate(all_data[:5]):
        print(f"  {i+1}. \"{item['text']}\" ({item['duration']:.1f}s)")

if __name__ == "__main__":
    main()
