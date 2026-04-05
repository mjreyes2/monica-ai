"""
Check audio files for corruption
"""
import os
import wave
import json
from pathlib import Path

def check_wav_file(file_path):
    """Check if a WAV file is corrupt."""
    try:
        with wave.open(str(file_path), 'rb') as wav_file:
            # Try to read basic properties
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            n_frames = wav_file.getnframes()

            # Try to read some frames
            wav_file.readframes(min(1024, n_frames))

            return {
                "status": "ok",
                "channels": channels,
                "sample_width": sample_width,
                "framerate": framerate,
                "duration": n_frames / framerate if framerate > 0 else 0
            }
    except Exception as e:
        return {
            "status": "corrupt",
            "error": str(e)
        }

def main():
    recordings_dir = Path("data/training/voice_training/recordings/MJP")

    if not recordings_dir.exists():
        print(f"❌ Directory not found: {recordings_dir}")
        return

    wav_files = list(recordings_dir.glob("*.wav"))

    print(f"\n{'='*60}")
    print(f"CHECKING {len(wav_files)} AUDIO FILES")
    print(f"{'='*60}\n")

    corrupt_files = []
    ok_files = []
    total_duration = 0

    for wav_file in wav_files:
        result = check_wav_file(wav_file)

        if result["status"] == "ok":
            ok_files.append(wav_file.name)
            total_duration += result["duration"]
        else:
            corrupt_files.append({
                "file": wav_file.name,
                "error": result["error"]
            })
            print(f"CORRUPT: {wav_file.name}")
            print(f"   Error: {result['error']}\n")

    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"OK files: {len(ok_files)}")
    print(f"Corrupt files: {len(corrupt_files)}")
    print(f"Total duration: {total_duration/60:.1f} minutes")
    print(f"{'='*60}\n")

    if corrupt_files:
        print("Corrupt files:")
        for item in corrupt_files:
            print(f"  - {item['file']}: {item['error']}")
    else:
        print("All audio files are valid!")

if __name__ == "__main__":
    main()
