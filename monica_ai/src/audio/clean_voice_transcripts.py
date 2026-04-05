"""
Clean voice training transcripts to remove unsupported characters.
Removes apostrophes, hyphens, and other special characters not in the vocabulary.
"""

import json
from pathlib import Path


def clean_text(text: str) -> str:
    """Clean text by removing or replacing unsupported characters."""
    # Convert to lowercase
    text = text.lower()

    # Remove apostrophes (don't -> dont, can't -> cant)
    text = text.replace("'", "")

    # Replace hyphens with space (non-stop -> non stop)
    text = text.replace("-", " ")

    # Remove any other special characters (keep only letters, numbers, spaces)
    cleaned = ""
    for char in text:
        if char.isalnum() or char == " ":
            cleaned += char

    # Collapse multiple spaces into one
    cleaned = " ".join(cleaned.split())

    return cleaned


def clean_manifest(manifest_path: Path):
    """Clean the manifest file."""
    print(f"Cleaning manifest: {manifest_path}")

    # Read all entries
    entries = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                original_text = entry['text']
                cleaned_text = clean_text(original_text)

                if original_text != cleaned_text:
                    print(f"  Changed: '{original_text}' -> '{cleaned_text}'")

                entry['text'] = cleaned_text
                entries.append(entry)

    # Write cleaned entries back
    with open(manifest_path, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

    print(f"[OK] Cleaned {len(entries)} entries")


def clean_csv(csv_path: Path):
    """Clean CSV file by updating the 'wrd' column."""
    import csv

    print(f"Cleaning CSV: {csv_path}")

    rows = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            original_text = row['wrd']
            cleaned_text = clean_text(original_text)

            if original_text != cleaned_text:
                print(f"  Changed: '{original_text}' -> '{cleaned_text}'")

            row['wrd'] = cleaned_text
            rows.append(row)

    # Write cleaned rows back
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        if rows:
            writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    print(f"[OK] Cleaned {len(rows)} entries")


if __name__ == "__main__":
    recordings_dir = Path("data/training/voice_training/recordings/MJP")

    # Clean manifest
    manifest_file = recordings_dir / "manifest.json"
    if manifest_file.exists():
        clean_manifest(manifest_file)
    else:
        print(f"Manifest not found: {manifest_file}")

    # Clean CSV files
    for csv_file in [recordings_dir / "train.csv", recordings_dir / "val.csv"]:
        if csv_file.exists():
            clean_csv(csv_file)
        else:
            print(f"CSV not found: {csv_file}")

    print("\n[OK] All files cleaned successfully!")
