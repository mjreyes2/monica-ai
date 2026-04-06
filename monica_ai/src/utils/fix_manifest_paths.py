"""
Fix manifest.json paths to use correct case (MJP not mjp)
"""
import json
from pathlib import Path

manifest_file = Path("data/training/recordings/wake_phrases/manifest.json")
print(f"Fixing paths in: {manifest_file}")

# Read all entries
entries = []
with open(manifest_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            entry = json.loads(line)
            # Fix the path case: replace /mjp/ with /MJP/
            entry['audio_filepath'] = entry['audio_filepath'].replace('/mjp/', '/MJP/').replace('\\mjp\\', '\\MJP\\')
            entries.append(entry)

print(f"Fixed {len(entries)} entries")

# Write back
with open(manifest_file, 'w', encoding='utf-8') as f:
    for entry in entries:
        f.write(json.dumps(entry) + '\n')

print("Done! Manifest paths fixed.")
print(f"Example: {entries[0]['audio_filepath']}")
