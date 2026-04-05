#!/usr/bin/env python3
"""
Reorganizes data/training into plain-English folder names.
Run once from project root: python reorganize_training.py
"""
import os
import shutil
from pathlib import Path

BASE = Path(__file__).parent / "data" / "training"

# ── 1. Create the new plain-English structure ──────────────────────────────
NEW_DIRS = [
    "DROP_WAKE_RECORDINGS_HERE",
    "DROP_SPEECH_RECORDINGS_HERE",
    "DROP_TTS_VOICE_SAMPLES_HERE",
    "_STT_Engine/datasets",
    "_STT_Engine/models",
    "_STT_Engine/scripts",
    "_TTS_Engine/datasets",
    "_TTS_Engine/models",
    "_TTS_Engine/scripts",
    "_Downloaded_Models",
]
print("Creating new folders...")
for d in NEW_DIRS:
    (BASE / d).mkdir(parents=True, exist_ok=True)
    print(f"  ✓ {d}")

# ── 2. Move wake phrase recordings ────────────────────────────────────────
def move_contents(src: Path, dst: Path, label: str):
    if not src.exists():
        print(f"  SKIP {label} (source does not exist)")
        return
    moved = 0
    for item in src.iterdir():
        target = dst / item.name
        if not target.exists():
            shutil.move(str(item), str(target))
            moved += 1
    print(f"  ✓ {label}: moved {moved} item(s)")

print("\nMoving recordings...")
move_contents(BASE / "recordings" / "wake_phrases",
              BASE / "DROP_WAKE_RECORDINGS_HERE",
              "wake phrases (recordings/wake_phrases)")
move_contents(BASE / "voice_training" / "recordings" / "MJP",
              BASE / "DROP_WAKE_RECORDINGS_HERE",
              "wake phrases (voice_training/recordings/MJP)")

print("\nMoving speech recordings...")
move_contents(BASE / "recordings" / "training_phrases",
              BASE / "DROP_SPEECH_RECORDINGS_HERE",
              "speech recordings (recordings/training_phrases)")
move_contents(BASE / "voice_recordings" / "training_phrases",
              BASE / "DROP_SPEECH_RECORDINGS_HERE",
              "speech recordings (voice_recordings/training_phrases)")
move_contents(BASE / "stt_training_recordings" / "incoming",
              BASE / "DROP_SPEECH_RECORDINGS_HERE",
              "speech recordings (stt_training_recordings/incoming)")
move_contents(BASE / "cache" / "stt_training_recordings",
              BASE / "DROP_SPEECH_RECORDINGS_HERE",
              "speech recordings (cache/stt_training_recordings)")

print("\nMoving STT engine...")
# Move monica_stt_training content into _STT_Engine
stt_src = BASE / "monica_stt_training"
if stt_src.exists():
    move_contents(stt_src / "datasets", BASE / "_STT_Engine" / "datasets", "STT datasets")
    move_contents(stt_src / "models",   BASE / "_STT_Engine" / "models",   "STT models")
    # Move root scripts
    for item in stt_src.iterdir():
        if item.is_file():
            target = BASE / "_STT_Engine" / "scripts" / item.name
            if not target.exists():
                shutil.move(str(item), str(target))
    print("  ✓ STT engine scripts moved")

print("\nMoving TTS engine...")
tts_src = BASE / "monica_tts_training"
if tts_src.exists():
    move_contents(tts_src / "datasets", BASE / "_TTS_Engine" / "datasets", "TTS datasets")
    move_contents(tts_src / "models",   BASE / "_TTS_Engine" / "models",   "TTS models")
    # Move root scripts and output
    for item in tts_src.iterdir():
        if item.is_file():
            target = BASE / "_TTS_Engine" / "scripts" / item.name
            if not target.exists():
                shutil.move(str(item), str(target))
    print("  ✓ TTS engine scripts moved")

print("\nMoving downloaded model cache...")
cache_src = BASE / "cache"
if cache_src.exists():
    for item in cache_src.iterdir():
        if item.name == "stt_training_recordings":
            continue  # already handled above
        target = BASE / "_Downloaded_Models" / item.name
        if not target.exists():
            shutil.move(str(item), str(target))
    print("  ✓ Model cache moved")

move_contents(BASE / "personal_voice_model",
              BASE / "_Downloaded_Models",
              "personal_voice_model")

print("\nMoving datasets/stt_combined → _STT_Engine/datasets/stt_combined...")
stt_comb_src = BASE / "datasets" / "stt_combined"
if stt_comb_src.exists():
    move_contents(stt_comb_src,
                  BASE / "_STT_Engine" / "datasets" / "stt_combined",
                  "stt_combined dataset")

# ── 3. Remove empty old folders ───────────────────────────────────────────
OLD_FOLDERS = [
    "recordings",
    "voice_training",
    "voice_recordings",
    "voice_training_combined",
    "personal_voice_model",
    "stt_training_recordings",
    "monica_stt_training",
    "monica_tts_training",
    "cache",
    "datasets",
    "models",
    "scripts",
]
print("\nRemoving empty old folders...")
for folder in OLD_FOLDERS:
    p = BASE / folder
    if p.exists():
        try:
            # Only remove if truly empty (recursively)
            remaining = list(p.rglob("*"))
            files = [f for f in remaining if f.is_file()]
            if not files:
                shutil.rmtree(str(p))
                print(f"  ✓ Removed empty: {folder}")
            else:
                print(f"  ⚠ Kept '{folder}' — still has {len(files)} file(s)")
        except Exception as e:
            print(f"  ✗ Could not remove {folder}: {e}")

# ── 4. Show final structure ────────────────────────────────────────────────
print("\n" + "="*60)
print("FINAL STRUCTURE:")
print("="*60)
for item in sorted(BASE.iterdir()):
    name = item.name
    if item.is_dir():
        count = len(list(item.rglob("*")))
        print(f"  📁 {name}/  ({count} items inside)")
    else:
        print(f"  📄 {name}")
print("="*60)
print("\nDone! Open data/training in Explorer to see the new layout.")
