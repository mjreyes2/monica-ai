import os
import soundfile as sf
import numpy as np
from pathlib import Path

OUTPUT_DIR = "data/training/recordings/training_phrases"

# Load phrases
with open("phrases.txt", "r", encoding="utf-8") as f:
    phrases = [line.strip() for line in f if line.strip()]

def get_filename(i, phrase):
    safe_phrase = phrase.replace(" ", "_").replace("'", "").replace(",", "")[:50]
    return os.path.join(OUTPUT_DIR, f"{i+1:04d}_{safe_phrase}.wav")

def analyze_audio(filename):
    """Analyze audio for speech presence using energy and zero-crossing rate."""
    try:
        data, sr = sf.read(filename)
        if len(data.shape) > 1:
            data = data[:, 0]  # Take first channel if stereo
        
        # Calculate metrics
        max_amp = np.max(np.abs(data))
        rms = np.sqrt(np.mean(data**2))
        
        # Zero crossing rate (speech typically has moderate ZCR)
        zero_crossings = np.sum(np.abs(np.diff(np.sign(data)))) / 2
        zcr = zero_crossings / len(data)
        
        # Calculate energy in frames
        frame_size = int(0.025 * sr)  # 25ms frames
        hop_size = int(0.010 * sr)    # 10ms hop
        
        num_frames = (len(data) - frame_size) // hop_size + 1
        if num_frames <= 0:
            return max_amp, rms, zcr, 0, 0
            
        energies = []
        for i in range(num_frames):
            start = i * hop_size
            frame = data[start:start + frame_size]
            energy = np.sum(frame ** 2)
            energies.append(energy)
        
        energies = np.array(energies)
        
        # Count frames with significant energy (likely speech)
        energy_threshold = np.mean(energies) * 0.1
        speech_frames = np.sum(energies > energy_threshold)
        speech_ratio = speech_frames / num_frames
        
        return max_amp, rms, zcr, speech_ratio, np.max(energies)
        
    except Exception as e:
        print(f"Error analyzing {filename}: {e}")
        return -1, -1, -1, -1, -1

def is_likely_silent(max_amp, rms, zcr, speech_ratio, max_energy):
    """Determine if recording likely has no speech."""
    # Very low amplitude = definitely silent
    if max_amp < 0.005:
        return True, "Very low amplitude"
    
    # Low RMS energy = likely silent
    if rms < 0.002:
        return True, "Very low RMS energy"
    
    # Very low speech ratio with low energy
    if speech_ratio < 0.1 and rms < 0.01:
        return True, "Low speech activity"
    
    return False, "OK"

print("Scanning all recordings for silent/no-speech files...")
print("=" * 70)

silent_files = []
good_files = []
all_files = list(Path(OUTPUT_DIR).glob("*.wav"))

print(f"Found {len(all_files)} total recordings\n")

for wav_file in sorted(all_files):
    max_amp, rms, zcr, speech_ratio, max_energy = analyze_audio(str(wav_file))
    
    if max_amp < 0:
        print(f"ERROR: {wav_file.name}")
        continue
    
    is_silent, reason = is_likely_silent(max_amp, rms, zcr, speech_ratio, max_energy)
    
    if is_silent:
        silent_files.append((wav_file, reason, max_amp, rms, speech_ratio))
        print(f"SILENT [{reason}]: {wav_file.name} (amp={max_amp:.4f}, rms={rms:.5f})")
    else:
        good_files.append(wav_file)

print("=" * 70)
print(f"\nResults:")
print(f"  Good recordings: {len(good_files)}")
print(f"  Silent/empty:    {len(silent_files)}")

if silent_files:
    print(f"\nSilent files to delete:")
    for f, reason, amp, rms, sr in silent_files:
        print(f"  - {f.name}")
    
    response = input("\nDelete these silent files? (yes/no): ").strip().lower()
    if response == 'yes':
        for f, _, _, _, _ in silent_files:
            os.remove(f)
            print(f"  Deleted: {f.name}")
        print(f"\nDeleted {len(silent_files)} silent files.")
    else:
        print("No files deleted.")
else:
    print("\nAll recordings contain speech!")
