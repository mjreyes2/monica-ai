"""
Test SpeechBrain ASR model on Monica's voice recordings.
This will show us how well the pretrained model works before fine-tuning.
"""

import json
from pathlib import Path
from speechbrain.inference.ASR import EncoderDecoderASR
import torch

print("="*60)
print("TESTING SPEECHBRAIN ASR ON MONICA'S VOICE")
print("="*60)

# Load recordings
recordings_dir = Path("voice_training/recordings/MJP")
manifest_file = recordings_dir / "manifest.json"

entries = []
with open(manifest_file) as f:
    for line in f:
        if line.strip():
            entries.append(json.loads(line))

# Use validation set for testing
val_entries = entries[int(len(entries) * 0.9):]

print(f"\n[INFO] Testing on {len(val_entries)} validation samples")
print(f"[GPU] {'Available' if torch.cuda.is_available() else 'Not available'}")

# Load pretrained model
print("\n[LOADING] SpeechBrain ASR model...")
asr_model = EncoderDecoderASR.from_hparams(
    source="speechbrain/asr-crdnn-rnnlm-librispeech",
    savedir="models/speechbrain_pretrained"
)
print("[SUCCESS] Model loaded")

# Test on validation samples
print("\n" + "="*60)
print("TESTING ACCURACY")
print("="*60)

correct = 0
total = len(val_entries)

for i, entry in enumerate(val_entries, 1):
    # Fix Windows path - use Path to normalize, then convert to forward slashes for soundfile
    audio_path_str = entry['audio_filepath'].replace('\\\\mjp\\\\', '\\\\MJP\\\\')
    audio_path = Path(audio_path_str)

    # Verify file exists
    if not audio_path.exists():
        print(f"[WARNING] File not found, skipping: {audio_path_str}")
        total -= 1
        continue

    expected = entry['text'].lower()

    # Convert to forward slashes for soundfile compatibility
    audio_path_posix = audio_path.as_posix()

    # Transcribe
    predicted = asr_model.transcribe_file(audio_path_posix).lower()

    # Check accuracy
    match = expected == predicted
    correct += 1 if match else 0

    status = "[OK]" if match else "[FAIL]"
    print(f"\n{status} Sample {i}/{total}")
    print(f"  Expected:  '{expected}'")
    print(f"  Predicted: '{predicted}'")

accuracy = (correct / total) * 100
print("\n" + "="*60)
print(f"ACCURACY: {accuracy:.1f}% ({correct}/{total} correct)")
print("="*60)

if accuracy < 80:
    print("\n[RECOMMENDATION] Accuracy is below 80% - fine-tuning recommended")
    print("The model needs to learn your specific voice patterns.")
elif accuracy < 95:
    print("\n[RECOMMENDATION] Good accuracy - light fine-tuning could improve it")
else:
    print("\n[SUCCESS] Excellent accuracy! Model works well with your voice.")

print(f"\n[INFO] Model saved at: models/speechbrain_pretrained")
print("[INFO] Ready to use with Monica!")
