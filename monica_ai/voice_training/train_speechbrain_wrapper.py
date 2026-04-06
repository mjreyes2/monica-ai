"""
Monica AI Voice Model Training - SpeechBrain Edition
Fine-tune wav2vec2 ASR model on your personal voice recordings using SpeechBrain.

This creates a highly accurate, personalized speech recognition model.
"""

import os
import json
import csv
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional, Tuple
import soundfile as sf


class SpeechBrainTrainer:
    """Train a personalized ASR model using SpeechBrain wav2vec2."""

    def __init__(self, recordings_dir: str = "data/training/recordings/wake_phrases"):
        """Initialize SpeechBrain trainer.

        Args:
            recordings_dir: Path to directory containing voice recordings and manifest
        """
        self.recordings_dir = Path(recordings_dir)
        self.manifest_file = self.recordings_dir / "manifest.json"

        # Find project root (where train_monica.py lives)
        self.project_root = Path(__file__).parent.parent.parent
        self.train_script = self.project_root / "train_monica.py"
        self.hparams_file = self.project_root / "hparams_monica.yaml"

        # Model output directory
        self.model_dir = self.project_root / "models" / "monica_finetuned"
        self.model_dir.mkdir(parents=True, exist_ok=True)

        print(f"[TRAINER] Recordings: {self.recordings_dir}")
        print(f"[TRAINER] Training script: {self.train_script}")
        print(f"[TRAINER] Model output: {self.model_dir}")

    def check_recordings(self) -> dict:
        """Check the status of recordings.

        Returns:
            dict with keys: count, duration, duration_minutes, ready, quality
        """
        if not self.manifest_file.exists():
            return {
                "count": 0,
                "duration": 0,
                "duration_minutes": 0.0,
                "ready": False,
                "quality": "insufficient",
            }

        count = 0
        total_duration = 0

        with open(self.manifest_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        count += 1
                        total_duration += entry.get('duration', 0)
                    except json.JSONDecodeError:
                        continue

        # For SpeechBrain with small dataset:
        # Need at least 10 recordings to start
        # 50+ for basic results
        # 100+ for good results
        ready = count >= 10

        return {
            "count": count,
            "duration": total_duration,
            "duration_minutes": round(total_duration / 60, 1),
            "ready": ready,
            "quality": self._get_quality_level(count)
        }

    def _get_quality_level(self, count: int) -> str:
        """Get expected quality level based on recording count."""
        if count < 10:
            return "insufficient"
        elif count < 50:
            return "basic"
        elif count < 100:
            return "good"
        elif count < 500:
            return "very_good"
        else:
            return "excellent"

    def prepare_data(self) -> Tuple[str, str]:
        """Prepare training and validation CSV files for SpeechBrain.

        Returns:
            Tuple of (train_csv_path, val_csv_path)
        """
        if not self.manifest_file.exists():
            raise FileNotFoundError("No manifest file found. Record some phrases first!")

        # Read all entries from manifest
        entries = []
        with open(self.manifest_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

        if len(entries) < 10:
            raise ValueError(f"Need at least 10 recordings, have {len(entries)}")

        # Split 90/10 for train/val (minimum 1 sample for validation)
        split_idx = max(1, int(len(entries) * 0.9))
        train_entries = entries[:split_idx]
        val_entries = entries[split_idx:]

        # Create CSV files in SpeechBrain format
        # Format: ID,duration,wav,wrd
        train_csv = self.recordings_dir / "train.csv"
        val_csv = self.recordings_dir / "val.csv"

        def write_csv(filepath: Path, data_entries: list):
            """Write CSV file in SpeechBrain format."""
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['ID', 'duration', 'wav', 'wrd'])

                for idx, entry in enumerate(data_entries):
                    audio_path = entry.get('audio_filepath', '')

                    # Make path absolute if it's relative
                    if audio_path and not Path(audio_path).is_absolute():
                        audio_path = str(self.recordings_dir / audio_path)

                    # Get duration from audio file
                    try:
                        if Path(audio_path).exists():
                            info = sf.info(audio_path)
                            duration = info.duration
                        else:
                            duration = entry.get('duration', 0)
                    except Exception:
                        duration = entry.get('duration', 0)

                    text = entry.get('text', '')
                    utterance_id = f"{filepath.stem}_{idx:05d}"

                    writer.writerow([utterance_id, duration, audio_path, text])

        write_csv(train_csv, train_entries)
        write_csv(val_csv, val_entries)

        print(f"[TRAINER] Training samples: {len(train_entries)}")
        print(f"[TRAINER] Validation samples: {len(val_entries)}")
        print(f"[TRAINER] Train CSV: {train_csv}")
        print(f"[TRAINER] Val CSV: {val_csv}")

        return str(train_csv), str(val_csv)

    def train(self, progress_callback: Optional[Callable[[float, str], None]] = None) -> Optional[str]:
        """Fine-tune the wav2vec2 ASR model on your voice.

        Args:
            progress_callback: Optional callable taking (percent: float, message: str)
                used by the GUI to display training progress.

        Returns:
            Path to the trained model directory, or None if training failed
        """
        print("\n" + "=" * 60)
        print("STARTING VOICE MODEL TRAINING (SpeechBrain + wav2vec2)")
        print("=" * 60)

        if progress_callback:
            progress_callback(0, "Preparing data...")

        # Prepare training data
        try:
            train_csv, val_csv = self.prepare_data()
        except Exception as e:
            print(f"[TRAINER] Error preparing data: {e}")
            if progress_callback:
                progress_callback(0, f"Error: {e}")
            return None

        if progress_callback:
            progress_callback(10, "Data prepared. Starting training...")

        # Check if training script exists
        if not self.train_script.exists():
            error_msg = f"Training script not found: {self.train_script}"
            print(f"[TRAINER] {error_msg}")
            if progress_callback:
                progress_callback(0, error_msg)
            return None

        if not self.hparams_file.exists():
            error_msg = f"Hyperparameters file not found: {self.hparams_file}"
            print(f"[TRAINER] {error_msg}")
            if progress_callback:
                progress_callback(0, error_msg)
            return None

        # Run training script as subprocess
        print(f"[TRAINER] Running: python {self.train_script} {self.hparams_file}")

        if progress_callback:
            progress_callback(15, "Training in progress (this may take 30-60 minutes)...")

        try:
            # Run training in subprocess
            process = subprocess.Popen(
                [sys.executable, str(self.train_script), str(self.hparams_file)],
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Monitor output for progress
            last_progress = 15
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())

                    # Update progress based on output patterns
                    if 'Epoch' in line and progress_callback:
                        # Try to extract epoch number
                        try:
                            if 'Epoch' in line and '/' in line:
                                parts = line.split('Epoch')[1].split('/')
                                current_epoch = int(parts[0].strip())
                                total_epochs = int(parts[1].split()[0].strip())
                                progress = 15 + (current_epoch / total_epochs * 75)
                                if progress > last_progress + 5:
                                    last_progress = progress
                                    progress_callback(progress, f"Training epoch {current_epoch}/{total_epochs}")
                        except Exception:
                            pass

                    elif 'loss' in line.lower() and progress_callback:
                        progress_callback(last_progress, "Training in progress...")

            # Wait for completion
            process.wait()

            if process.returncode == 0:
                print("[TRAINER] Training completed successfully!")

                # Find the saved model
                # SpeechBrain saves to models/monica_finetuned/<seed>/save
                model_path = self.model_dir / "1986" / "save"

                if model_path.exists():
                    if progress_callback:
                        progress_callback(100, "Training complete!")
                    print(f"[TRAINER] Model saved to: {model_path}")
                    return str(model_path)
                else:
                    # Check for any subdirectories
                    subdirs = list(self.model_dir.glob("*/save"))
                    if subdirs:
                        model_path = subdirs[0]
                        if progress_callback:
                            progress_callback(100, "Training complete!")
                        print(f"[TRAINER] Model saved to: {model_path}")
                        return str(model_path)
                    else:
                        if progress_callback:
                            progress_callback(90, "Training complete, but model path not found")
                        return str(self.model_dir)
            else:
                error_msg = f"Training failed with return code {process.returncode}"
                print(f"[TRAINER] {error_msg}")
                if progress_callback:
                    progress_callback(0, error_msg)
                return None

        except Exception as e:
            error_msg = f"Error during training: {e}"
            print(f"[TRAINER] {error_msg}")
            if progress_callback:
                progress_callback(0, error_msg)
            return None


# Alias for backward compatibility with GUI
VoiceModelTrainer = SpeechBrainTrainer


if __name__ == "__main__":
    # Test the trainer
    trainer = SpeechBrainTrainer()

    status = trainer.check_recordings()
    print(f"\nRecording Status:")
    print(f"  Count: {status['count']}")
    print(f"  Duration: {status['duration_minutes']} minutes")
    print(f"  Ready: {status['ready']}")
    print(f"  Quality: {status['quality']}")

    if status['ready']:
        print("\nReady to train! Run trainer.train() to start.")
    else:
        print(f"\nNeed more recordings. Have {status['count']}, need at least 10.")
