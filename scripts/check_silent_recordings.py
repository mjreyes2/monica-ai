import os
import soundfile as sf
import numpy as np

OUTPUT_DIR = "data/training/recordings/training_phrases"

# Load phrases
with open("phrases.txt", "r", encoding="utf-8") as f:
    phrases = [line.strip() for line in f if line.strip()]

def get_filename(i, phrase):
    safe_phrase = phrase.replace(" ", "_").replace("'", "").replace(",", "")[:50]
    return os.path.join(OUTPUT_DIR, f"{i+1:04d}_{safe_phrase}.wav")

def check_audio_level(filename):
    """Returns max amplitude of audio file. Silent files have very low values."""
    try:
        data, sr = sf.read(filename)
        max_amp = np.max(np.abs(data))
        rms = np.sqrt(np.mean(data**2))
        return max_amp, rms
    except Exception as e:
        return -1, -1

silent_files = []
print("Scanning recordings for silent files...")
print("=" * 60)

for i, phrase in enumerate(phrases):
    filename = get_filename(i, phrase)
    if os.path.exists(filename):
        max_amp, rms = check_audio_level(filename)
        # Consider silent if max amplitude < 0.01 or RMS < 0.001
        if max_amp < 0.01 or rms < 0.001:
            silent_files.append((i + 1, phrase, max_amp, rms))
            print(f"[{i+1}] SILENT (max={max_amp:.4f}, rms={rms:.6f}): {phrase[:50]}")

print("=" * 60)
print(f"\nFound {len(silent_files)} silent/empty recordings out of recorded files.")

if silent_files:
    # Save list of phrase numbers to re-record
    with open("rerecord_list.txt", "w", encoding="utf-8") as f:
        for num, phrase, _, _ in silent_files:
            f.write(f"{num}\n")
    print(f"\nSaved phrase numbers to rerecord_list.txt")
    print("\nPhrase numbers to re-record:")
    print([num for num, _, _, _ in silent_files])
