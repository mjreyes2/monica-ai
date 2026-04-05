#!/usr/bin/env python3
"""
Update all code references from old folder structure to new consolidated structure.
"""

import os
import re
from pathlib import Path

# Path mappings: OLD -> NEW
PATH_MAPPINGS = {
    # Old paths components
    "voice_training/recordings/MJP": "recordings/wake_phrases",
    "voice_recordings/training_phrases": "recordings/training_phrases",
    "voice_training_combined": "datasets/stt_combined",
    "personal_voice_model": "cache",
    "monica_tts_training/datasets": "datasets/tts_corpora",
    "monica_tts_training/models": "models/tts",
    "monica_tts_training": "scripts/tts",
    "monica_stt_training": "scripts/stt",
    "stt_training_recordings": "recordings/training_phrases",  # Consolidate legacy
}

# Files to update
ROOT = Path(__file__).resolve().parent.parent
SEARCH_PATTERNS = [
    "src/**/*.py",
    "scripts/**/*.py",
    "monica_ai/**/*.py",
]

def update_file(file_path: Path) -> int:
    """Update a single file. Return number of replacements."""
    try:
        content = file_path.read_text(encoding="utf-8")
        original = content
        
        # Replace each mapping
        for old, new in PATH_MAPPINGS.items():
            # Match various quote types and path separators
            patterns = [
                (rf'"{old}"', f'"{new}"'),
                (rf"'{old}'", f"'{new}'"),
                (rf"`{old}`", f"`{new}`"),
                (rf'"{old.replace("/", "\\\\")}"', f'"{new.replace("/", "\\\\")}"'),
                (rf"'{old.replace('/', '\\\\')}'", f"'{new.replace('/', '\\\\')}'"),
            ]
            
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            
            # Also handle path joins like Path(...) / "voice_training" / ...
            content = content.replace(f'/ "{old}"', f'/ "{new}"')
            content = content.replace(f"/ '{old}'", f"/ '{new}'")
        
        if content != original:
            file_path.write_text(content, encoding="utf-8")
            count = len([i for i, (o, n) in enumerate(re.findall(r'(voice_training|voice_recordings|personal_voice_model|monica_tts_training|monica_stt_training|stt_training_recordings)', original)) if i < len(content)])
            return 1  # At least one change
        return 0
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return 0

def main():
    print("=" * 70)
    print("UPDATING CODE REFERENCES")
    print("=" * 70)
    
    updated_count = 0
    file_count = 0
    
    for pattern in SEARCH_PATTERNS:
        for file_path in ROOT.glob(pattern):
            if file_path.is_file() and file_path.suffix == ".py":
                if update_file(file_path):
                    print(f"✓ Updated: {file_path.relative_to(ROOT)}")
                    updated_count += 1
                file_count += 1
    
    print(f"\n{'=' * 70}")
    print(f"Summary: {updated_count} files updated out of {file_count} Python files scanned")
    print("=" * 70)

if __name__ == "__main__":
    main()
