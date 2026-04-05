"""
Create an enhanced voice signature from your voice recordings.
This script uses SpeechBrain's speaker recognition model to create a
highly accurate voice signature from your recordings in the 'voice_recordings' directory.
"""
import torch
import torchaudio
from pathlib import Path
import numpy as np
from speechbrain.inference.speaker import SpeakerRecognition

def create_voice_signature():
    """
    Creates an enhanced voice signature from recordings in the 'voice_recordings' directory.
    """
    print("=" * 60)
    print("CREATING ENHANCED VOICE SIGNATURE")
    print("=" * 60)

    # Configuration
    script_dir = Path(__file__).parent
    model_dir = script_dir / "personal_voice_model"
    model_dir.mkdir(exist_ok=True)
    recordings_dir = script_dir / "voice_recordings"
    output_file = model_dir / "enhanced_voice_signature.pt"

    if not recordings_dir.exists() or not any(recordings_dir.iterdir()):
        print(f"Error: The '{recordings_dir}' directory is empty or does not exist.")
        print("Please record your voice first using a recording script.")
        return

    try:
        # Load the speaker recognition model
        print("1. Loading Speaker Recognition Model...")
        speaker_model = SpeakerRecognition.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir=model_dir / "speaker_model",
            run_opts={"device": "cuda" if torch.cuda.is_available() else "cpu"}
        )
        print("   Success: Model loaded successfully.")

        # Get all .wav files from the recordings directory
        audio_files = list(recordings_dir.glob("*.wav"))
        if not audio_files:
            print(f"Error: No .wav files found in '{recordings_dir}'.")
            return

        print(f"\n2. Processing {len(audio_files)} voice recordings...")

        all_embeddings = []
        for audio_file in audio_files:
            try:
                # Load and process the audio file
                waveform, sample_rate = torchaudio.load(audio_file)

                if sample_rate != 16000:
                    resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
                    waveform = resampler(waveform)

                # Generate the embedding
                embedding = speaker_model.encode_batch(waveform)
                all_embeddings.append(embedding.squeeze(0))
                print(f"   - Processed: {audio_file.name}")

            except Exception as e:
                print(f"   Warning: Could not process {audio_file.name}. Error: {e}")

        if not all_embeddings:
            print("Error: Could not generate any embeddings from the audio files.")
            return

        # Average the embeddings to create a robust voice signature
        print("\n3. Averaging embeddings to create voice signature...")
        voice_signature = torch.mean(torch.stack(all_embeddings), dim=0)
        print("   Success: Voice signature created.")

        # Save the voice signature
        print(f"\n4. Saving voice signature to: {output_file}")
        torch.save({'voice_signature': voice_signature}, output_file)
        print("   Success: Signature saved successfully!")

        print("\n" + "=" * 60)
        print("Success: Voice signature creation complete!")
        print("Monica will now use this signature for speaker verification.")
        print("=" * 60)

    except ImportError:
        print("Error: SpeechBrain is not installed. Please run: pip install speechbrain")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    create_voice_signature()
