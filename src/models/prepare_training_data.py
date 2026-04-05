"""
Prepare training data by combining existing recordings with new phrase recordings.
Creates train.csv and val.csv for SpeechBrain training.
"""

import os
import json
import csv
import soundfile as sf
import random
from pathlib import Path

# Paths
PROJECT_DIR = Path("C:/Monica")
TRAINING_DIR = PROJECT_DIR / "data" / "training"
NEW_RECORDINGS_DIR = TRAINING_DIR / "voice_recordings" / "training_phrases"
EXISTING_MANIFEST = TRAINING_DIR / "voice_training" / "recordings" / "MJP" / "train_manifest.json"
OUTPUT_DIR = TRAINING_DIR / "voice_training" / "recordings" / "MJP"
PHRASES_FILE = PROJECT_DIR / "phrases.txt"

# Load phrases for transcription lookup
print("Loading phrases...")
with open(PHRASES_FILE, "r", encoding="utf-8") as f:
    phrases = [line.strip().lower() for line in f if line.strip()]

def get_audio_duration(filepath):
    """Get duration of audio file in seconds."""
    try:
        info = sf.info(filepath)
        return info.duration
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def clean_transcription(text):
    """Clean transcription to only contain a-z and space (for CTC character vocabulary)."""
    import re
    # Convert to lowercase
    text = text.lower()
    # Replace apostrophes with nothing (don't -> dont, it's -> its)
    text = text.replace("'", "")
    text = text.replace("'", "")  # curly apostrophe
    # Keep only a-z and space
    text = re.sub(r'[^a-z ]', '', text)
    # Collapse multiple spaces
    text = re.sub(r' +', ' ', text)
    return text.strip()

def extract_transcription_from_filename(filename):
    """Extract transcription from filename like '0001_The_quick_brown_fox.wav'"""
    # Remove extension and number prefix
    name = Path(filename).stem
    parts = name.split("_", 1)  # Split on first underscore
    if len(parts) > 1:
        # Replace underscores with spaces and clean up
        text = parts[1].replace("_", " ").lower()
        # Remove any trailing numbers or extra characters
        return clean_transcription(text)
    return clean_transcription(name.lower())

def load_existing_data():
    """Load existing training manifest."""
    existing_data = []
    if EXISTING_MANIFEST.exists():
        print(f"Loading existing manifest from {EXISTING_MANIFEST}")
        with open(EXISTING_MANIFEST, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        # Verify file exists
                        if os.path.exists(entry["audio_filepath"]):
                            existing_data.append({
                                "ID": Path(entry["audio_filepath"]).stem,
                                "wav": entry["audio_filepath"],
                                "wrd": entry["text"].lower(),
                                "duration": entry.get("duration", 0)
                            })
                    except json.JSONDecodeError:
                        continue
        print(f"Loaded {len(existing_data)} existing recordings")
    return existing_data

def load_new_recordings():
    """Load new phrase recordings."""
    new_data = []
    print(f"\nScanning new recordings from {NEW_RECORDINGS_DIR}")
    
    wav_files = sorted(NEW_RECORDINGS_DIR.glob("*.wav"))
    print(f"Found {len(wav_files)} new recordings")
    
    for wav_file in wav_files:
        # Extract phrase number from filename (e.g., "0001_..." -> 0)
        try:
            phrase_num = int(wav_file.stem.split("_")[0]) - 1  # 0-indexed
            if 0 <= phrase_num < len(phrases):
                transcription = clean_transcription(phrases[phrase_num])
            else:
                transcription = extract_transcription_from_filename(wav_file.name)
        except (ValueError, IndexError):
            transcription = extract_transcription_from_filename(wav_file.name)
        
        duration = get_audio_duration(str(wav_file))
        if duration is None or duration < 0.1:
            print(f"Skipping {wav_file.name} - invalid duration")
            continue
        
        new_data.append({
            "ID": wav_file.stem,
            "wav": str(wav_file.absolute()),
            "wrd": transcription,
            "duration": duration
        })
    
    print(f"Loaded {len(new_data)} new recordings")
    return new_data

def write_csv(data, output_path):
    """Write data to CSV in SpeechBrain format."""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "wav", "wrd", "duration"])
        for entry in data:
            writer.writerow([entry["ID"], entry["wav"], entry["wrd"], entry["duration"]])
    print(f"Wrote {len(data)} entries to {output_path}")

def main():
    print("="*60)
    print("PREPARING TRAINING DATA")
    print("="*60)
    
    # Load all data
    existing_data = load_existing_data()
    new_data = load_new_recordings()
    
    # Combine all data
    all_data = existing_data + new_data
    print(f"\nTotal recordings: {len(all_data)}")
    print(f"  - Existing: {len(existing_data)}")
    print(f"  - New phrases: {len(new_data)}")
    
    # Calculate total duration
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
    
    # Write CSV files
    train_csv = OUTPUT_DIR / "train.csv"
    val_csv = OUTPUT_DIR / "val.csv"
    
    write_csv(train_data, train_csv)
    write_csv(val_data, val_csv)
    
    # Also create a combined manifest for reference
    combined_manifest = OUTPUT_DIR / "combined_manifest.json"
    with open(combined_manifest, "w", encoding="utf-8") as f:
        for entry in all_data:
            json.dump({
                "audio_filepath": entry["wav"],
                "text": entry["wrd"],
                "duration": entry["duration"]
            }, f)
            f.write("\n")
    print(f"Wrote combined manifest to {combined_manifest}")
    
    print("\n" + "="*60)
    print("DATA PREPARATION COMPLETE")
    print("="*60)
    print(f"\nReady for training with:")
    print(f"  train_csv: {train_csv}")
    print(f"  valid_csv: {val_csv}")

if __name__ == "__main__":
    main()
