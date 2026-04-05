"""
Create training CSV files from manifest.json for SpeechBrain training
"""
import json
import csv
import re
from pathlib import Path

# Paths
project_root = Path(__file__).parent.parent  # Go up from scripts/ to project root
manifest_dir = project_root / "data" / "training" / "datasets" / "stt_combined"
manifest_file = manifest_dir / "train.json"  # Use existing combined manifest

print("Creating training CSVs from manifest...")
print(f"Reading: {manifest_file}")

# Load manifest (supports JSONL and JSON array, with optional UTF-8 BOM)
entries = []
with open(manifest_file, 'r', encoding='utf-8-sig') as f:
    content = f.read().strip()

if content.startswith('['):
    parsed = json.loads(content)
    if isinstance(parsed, list):
        entries.extend(parsed)
else:
    for line in content.splitlines():
        line = line.strip()
        if line:
            entries.append(json.loads(line))

print(f"Found {len(entries)} recordings")

# Split data (90/10)
split_idx = int(len(entries) * 0.9)
train_entries = entries[:split_idx]
val_entries = entries[split_idx:]

print(f"Training: {len(train_entries)} samples")
print(f"Validation: {len(val_entries)} samples")


def _is_wake_phrase(text: str) -> bool:
    t = (text or "").lower().strip()
    t = re.sub(r"\s+", " ", t)
    has_monica = any(x in t for x in ("monica", "monika", "omega", "monic"))
    has_init = any(x in t for x in (
        "initialize", "initialise", "initializing", "initialising", "init",
        "interlaced", "in itialize", "startup", "start up", "activate"
    ))
    return has_monica and has_init


# Boost wake phrase samples in training split for stronger activation accuracy.
wake_entries = [e for e in train_entries if _is_wake_phrase(e.get('text', ''))]
if wake_entries:
    wake_boost_factor = 4
    train_entries = train_entries + (wake_entries * wake_boost_factor)
    print(f"Wake phrase boost: +{len(wake_entries) * wake_boost_factor} samples ({len(wake_entries)} base x{wake_boost_factor})")
else:
    print("Wake phrase boost: no wake samples found in manifest")

# Create CSV function
def create_csv(entries, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'duration', 'wav', 'wrd'])
        for i, entry in enumerate(entries):
            # Use Path to ensure correct case and convert to forward slashes
            from pathlib import Path
            audio_field = entry.get('audio')
            if isinstance(audio_field, dict):
                audio_path = audio_field.get('path', '')
            elif isinstance(audio_field, str):
                audio_path = audio_field
            else:
                audio_path = ''
            wav_value = (
                entry.get('audio_filepath')
                or entry.get('wav')
                or audio_path
                or ''
            )
            text_value = entry.get('text') or entry.get('wrd') or ''
            duration_value = entry.get('duration', 0.0)
            if isinstance(duration_value, str):
                try:
                    duration_value = float(duration_value)
                except ValueError:
                    duration_value = 0.0
            wav_path = Path(str(wav_value)).as_posix()
            writer.writerow([
                f"sample_{i:04d}",
                duration_value,
                wav_path,
                text_value
            ])

# Create CSVs
train_csv = manifest_dir / "train.csv"
val_csv = manifest_dir / "val.csv"

create_csv(train_entries, train_csv)
create_csv(val_entries, val_csv)

print(f"Created: {train_csv}")
print(f"Created: {val_csv}")
print("Done!")
