"""
Clean manifest.json - remove entries for files that don't exist
"""
import json
from pathlib import Path

manifest_file = Path("data/training/recordings/wake_phrases/manifest.json")
print(f"Cleaning manifest: {manifest_file}")

# Read all entries
entries = []
removed = 0
with open(manifest_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            entry = json.loads(line)
            # Check if file exists
            audio_file = Path(entry['audio_filepath'])
            if audio_file.exists():
                entries.append(entry)
            else:
                print(f"Removing missing file: {audio_file.name}")
                removed += 1

print(f"\nKept {len(entries)} entries")
print(f"Removed {removed} missing files")

# Write cleaned manifest
with open(manifest_file, 'w', encoding='utf-8') as f:
    for entry in entries:
        f.write(json.dumps(entry) + '\n')

print("Done! Manifest cleaned.")
