"""
Voice Enrollment for Monica AI — Speaker Verification
======================================================
Records several samples of the user's voice, extracts speaker embeddings
using SpeechBrain's ECAPA-TDNN model, and stores the averaged embedding
as `enhanced_voice_signature.pt`.

Once enrolled, Monica's STT pipeline will reject audio from unknown
speakers, only transcribing commands from the enrolled voice.

Usage:
    python enroll_voice.py
"""

import sys, time, os
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_DIR = PROJECT_ROOT / "data" / "training" / "personal_voice_model"
SIGNATURE_FILE = MODEL_DIR / "enhanced_voice_signature.pt"
SPEAKER_CACHE = MODEL_DIR / "speaker_cached"


def record_clip(duration: float = 4.0, sample_rate: int = 16000) -> np.ndarray:
    """Record a short audio clip from the default microphone."""
    import pyaudio

    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paFloat32,
        channels=1,
        rate=sample_rate,
        input=True,
        frames_per_buffer=1024,
    )

    print(f"  Recording for {duration:.0f} seconds... speak now!")
    frames = []
    for _ in range(int(sample_rate / 1024 * duration)):
        data = stream.read(1024, exception_on_overflow=False)
        frames.append(np.frombuffer(data, dtype=np.float32))

    stream.stop_stream()
    stream.close()
    pa.terminate()

    audio = np.concatenate(frames)
    print(f"  Recorded {len(audio)/sample_rate:.1f}s ({len(audio)} samples)")
    return audio


def main():
    print("=" * 60)
    print("  Monica AI — Voice Enrollment")
    print("=" * 60)
    print()
    print("This will record your voice and create a speaker profile")
    print("so Monica only responds to YOUR voice.\n")

    # Ensure dirs exist
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    SPEAKER_CACHE.mkdir(parents=True, exist_ok=True)

    # Load SpeechBrain speaker model
    print("[1/3] Loading speaker recognition model...")
    import torch
    from speechbrain.inference.speaker import SpeakerRecognition

    device = "cuda" if torch.cuda.is_available() else "cpu"
    speaker_model: SpeakerRecognition = SpeakerRecognition.from_hparams(  # type: ignore[assignment]
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir=str(SPEAKER_CACHE),
        run_opts={"device": device},
    )
    print(f"  Speaker model loaded on {device}\n")

    # Collect voice samples
    num_samples = 5
    embeddings = []

    print(f"[2/3] Recording {num_samples} voice samples.")
    print("  Please say a different sentence each time.\n")

    prompts = [
        'Say: "Monica, initialize all systems."',
        'Say: "Show me the globe and zoom in on Tokyo."',
        'Say: "What is the temperature outside today?"',
        'Say: "Tell me about the history of ancient Egypt."',
        'Say: "Monica, identify the objects in front of me."',
    ]

    for i in range(num_samples):
        print(f"--- Sample {i+1}/{num_samples} ---")
        print(f"  {prompts[i]}")
        input("  Press ENTER when ready... ")

        audio = record_clip(duration=4.0, sample_rate=16000)

        # Check there's actual energy (not silence)
        energy = np.mean(np.abs(audio))
        if energy < 0.005:
            print("  WARNING: Very quiet recording. Please speak louder.\n")
            continue

        audio_tensor = torch.from_numpy(audio).float().unsqueeze(0)
        embedding = speaker_model.encode_batch(audio_tensor)
        embeddings.append(embedding.squeeze().cpu())
        print(f"  Embedding extracted (energy: {energy:.4f})\n")

    if len(embeddings) < 3:
        print("ERROR: Need at least 3 valid samples. Please try again.")
        sys.exit(1)

    # Average embeddings to create robust voice signature
    print(f"[3/3] Creating voice signature from {len(embeddings)} samples...")
    stacked = torch.stack(embeddings)
    voice_signature = torch.mean(stacked, dim=0)
    # Normalize
    voice_signature = voice_signature / voice_signature.norm()

    # Save
    torch.save({"voice_signature": voice_signature}, str(SIGNATURE_FILE))
    print(f"  Voice signature saved to: {SIGNATURE_FILE}")
    print(f"  Embedding dimension: {voice_signature.shape}")

    # Verify by testing against the samples
    print("\n  Verification test:")
    for i, emb in enumerate(embeddings):
        sim = torch.nn.functional.cosine_similarity(
            emb.unsqueeze(0), voice_signature.unsqueeze(0)
        ).item()
        print(f"    Sample {i+1}: similarity = {sim:.3f} {'✓' if sim >= 0.25 else '✗'}")

    print("\n" + "=" * 60)
    print("  Enrollment complete!")
    print("  Monica will now only respond to your voice.")
    print("  Re-run this script to re-enroll at any time.")
    print("=" * 60)


if __name__ == "__main__":
    main()
