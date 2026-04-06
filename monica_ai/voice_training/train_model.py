"""
Monica AI Voice Model Training
Fine-tune NVIDIA NeMo ASR on your personal voice recordings.

This creates a highly accurate, personalized speech recognition model.
"""

import os
import json
from pathlib import Path

# Check for NeMo (now expected to be installed as nemo_toolkit)
import nemo
import nemo.collections.asr as nemo_asr
from nemo.collections.asr.models import EncDecCTCModel
from nemo.utils import logging
HAS_NEMO = True

import torch


class VoiceModelTrainer:
    """Train a personalized ASR model using NeMo."""
    
    def __init__(self, recordings_dir: str = "data/training/recordings/wake_phrases"):
        """Initialize trainer.

        Default recordings_dir now points at the user-specific folder used by
        the GUI (voice_training/recordings/MJP) so that running this module
        directly from the project root will see your existing manifest and
        recordings.
        """
        self.recordings_dir = Path(recordings_dir)
        self.manifest_file = self.recordings_dir / "manifest.json"
        self.model_dir = Path("models/nemo_personal")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Training config
        # Use a base model that is known to exist in this NeMo install.
        # From your list_available_models() output, stt_en_conformer_ctc_small
        # is present, so we use that as the starting ASR model.
        self.base_model = "stt_en_conformer_ctc_small"  # Small English Conformer CTC
        self.epochs = 50
        self.batch_size = 8
        self.learning_rate = 1e-4
        
        print(f"[TRAINER] Recordings: {self.recordings_dir}")
        print(f"[TRAINER] Model output: {self.model_dir}")
    
    def check_recordings(self) -> dict:
        """Check the status of recordings."""
        if not self.manifest_file.exists():
            # Always return the full status schema so callers don't KeyError
            return {
                "count": 0,
                "duration": 0,
                "duration_minutes": 0.0,
                "ready": False,
                "quality": "insufficient",
            }
        
        count = 0
        total_duration = 0
        
        with open(self.manifest_file, 'r') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    count += 1
                    total_duration += entry.get('duration', 0)
        
        # Need at least 100 recordings (~10 minutes) for basic training
        # 500+ recordings (~1 hour) for good results
        # 1000+ recordings (~2 hours) for excellent results
        ready = count >= 100
        
        return {
            "count": count,
            "duration": total_duration,
            "duration_minutes": round(total_duration / 60, 1),
            "ready": ready,
            "quality": self._get_quality_level(count)
        }
    
    def _get_quality_level(self, count: int) -> str:
        """Get expected quality level based on recording count."""
        if count < 100:
            return "insufficient"
        elif count < 300:
            return "basic"
        elif count < 500:
            return "good"
        elif count < 800:
            return "very_good"
        else:
            return "excellent"
    
    def prepare_data(self):
        """Prepare training and validation data."""
        if not self.manifest_file.exists():
            raise FileNotFoundError("No manifest file found. Record some phrases first!")
        
        # Read all entries
        entries = []
        with open(self.manifest_file, 'r') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        
        if len(entries) < 100:
            raise ValueError(f"Need at least 100 recordings, have {len(entries)}")
        
        # Split 90/10 for train/val
        split_idx = int(len(entries) * 0.9)
        train_entries = entries[:split_idx]
        val_entries = entries[split_idx:]
        
        # Write split manifests
        train_manifest = self.recordings_dir / "train_manifest.json"
        val_manifest = self.recordings_dir / "val_manifest.json"
        
        with open(train_manifest, 'w') as f:
            for entry in train_entries:
                f.write(json.dumps(entry) + '\n')
        
        with open(val_manifest, 'w') as f:
            for entry in val_entries:
                f.write(json.dumps(entry) + '\n')
        
        print(f"[TRAINER] Training samples: {len(train_entries)}")
        print(f"[TRAINER] Validation samples: {len(val_entries)}")
        
        return str(train_manifest), str(val_manifest)
    
    def train(self, progress_callback=None):
        """Fine-tune the ASR model on your voice.

        Args:
            progress_callback: Optional callable taking (percent: float, message: str)
                used by the GUI to display training progress.
        """
        if not HAS_NEMO:
            print("ERROR: NeMo not installed!")
            print("Run: pip install nemo_toolkit[asr]")
            return
        
        print("\n" + "=" * 60)
        print("STARTING VOICE MODEL TRAINING")
        print("=" * 60)
        if progress_callback:
            progress_callback(5.0, "Initializing trainer...")
        
        # Check GPU
        if torch.cuda.is_available():
            print(f"[GPU] {torch.cuda.get_device_name(0)}")
            print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        else:
            print("[WARNING] No GPU detected - training will be slow")
        
        # Prepare data
        if progress_callback:
            progress_callback(15.0, "Preparing data and manifests...")
        train_manifest, val_manifest = self.prepare_data()
        
        # Load pre-trained model
        print(f"\n[TRAINER] Loading base model: {self.base_model}")
        if progress_callback:
            progress_callback(30.0, "Loading base NeMo model...")
        model = nemo_asr.models.ASRModel.from_pretrained(self.base_model)

        # Update data config
        model.cfg.train_ds.manifest_filepath = train_manifest
        model.cfg.validation_ds.manifest_filepath = val_manifest
        model.cfg.train_ds.batch_size = self.batch_size
        model.cfg.validation_ds.batch_size = self.batch_size

        # Setup data loaders before training
        model.setup_training_data(model.cfg.train_ds)
        model.setup_validation_data(model.cfg.validation_ds)
        
        # Setup trainer
        from pytorch_lightning import Trainer
        from pytorch_lightning.callbacks import ModelCheckpoint

        checkpoint_callback = ModelCheckpoint(
            dirpath=str(self.model_dir / "checkpoints"),
            filename="monica_voice_{epoch:02d}_{val_loss:.2f}",
            save_top_k=3,
            monitor="val_loss",
            mode="min"
        )

        if progress_callback:
            progress_callback(45.0, "Configuring trainer and optimizer...")

        trainer = Trainer(
            max_epochs=self.epochs,
            accelerator="gpu" if torch.cuda.is_available() else "cpu",
            devices=1,
            callbacks=[checkpoint_callback],
            enable_progress_bar=True,
            log_every_n_steps=10
        )

        # Set trainer in model BEFORE setup_optimization
        model.set_trainer(trainer)

        # Setup optimizer
        model.setup_optimization(
            optim_config={
                "name": "adam",
                "lr": self.learning_rate,
                "weight_decay": 0.0001
            }
        )

        # Train!
        print("\n[TRAINER] Starting training...")
        print(f"   Epochs: {self.epochs}")
        print(f"   Batch size: {self.batch_size}")
        print(f"   Learning rate: {self.learning_rate}")
        print("\n" + "-" * 60)
        if progress_callback:
            progress_callback(60.0, "Training in progress...")

        trainer.fit(model)
        
        # Save final model
        if progress_callback:
            progress_callback(90.0, "Saving trained model...")
        final_model_path = self.model_dir / "monica_voice_model.nemo"
        model.save_to(str(final_model_path))
        
        print("\n" + "=" * 60)
        print("[SUCCESS] TRAINING COMPLETE!")
        print(f"   Model saved to: {final_model_path}")
        print("=" * 60)
        if progress_callback:
            progress_callback(100.0, f"Training complete. Model saved to: {final_model_path}")
        
        return str(final_model_path)
    
    def test_model(self, audio_file: str = None):
        """Test the trained model."""
        model_path = self.model_dir / "monica_voice_model.nemo"
        
        if not model_path.exists():
            print("No trained model found. Train first!")
            return
        
        print(f"[TRAINER] Loading model: {model_path}")
        model = nemo_asr.models.ASRModel.restore_from(str(model_path))
        
        if audio_file:
            # Test specific file
            result = model.transcribe([audio_file])
            print(f"Transcription: {result[0]}")
        else:
            # Test with validation set
            val_manifest = self.recordings_dir / "val_manifest.json"
            if val_manifest.exists():
                with open(val_manifest, 'r') as f:
                    entries = [json.loads(line) for line in f if line.strip()]
                
                print("\nTesting on validation samples:")
                print("-" * 60)
                
                correct = 0
                total = min(10, len(entries))  # Test first 10
                
                for entry in entries[:total]:
                    audio_path = entry['audio_filepath']
                    expected = entry['text']
                    
                    result = model.transcribe([audio_path])
                    predicted = result[0].lower()
                    
                    match = "[OK]" if predicted == expected else "[FAIL]"
                    correct += 1 if predicted == expected else 0
                    
                    print(f"{match} Expected: '{expected}'")
                    print(f"   Got:      '{predicted}'")
                    print()
                
                accuracy = (correct / total) * 100
                print(f"Accuracy: {accuracy:.1f}% ({correct}/{total})")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train Monica voice model")
    parser.add_argument("--check", action="store_true", help="Check recording status")
    parser.add_argument("--train", action="store_true", help="Start training")
    parser.add_argument("--test", action="store_true", help="Test the model")
    parser.add_argument("--audio", type=str, help="Audio file to test")
    
    args = parser.parse_args()
    
    trainer = VoiceModelTrainer()
    
    if args.check:
        status = trainer.check_recordings()
        print("\n" + "=" * 60)
        print("RECORDING STATUS")
        print("=" * 60)
        print(f"  Recordings: {status['count']}")
        print(f"  Duration: {status['duration_minutes']} minutes")
        print(f"  Quality level: {status['quality']}")
        ready_status = "Yes" if status['ready'] else "No (need 100+)"
        print(f"  Ready to train: {ready_status}")
        print("=" * 60)
        
    elif args.train:
        trainer.train()
        
    elif args.test:
        trainer.test_model(args.audio)
        
    else:
        # Default: show status
        status = trainer.check_recordings()
        print("\n" + "=" * 60)
        print("MONICA VOICE MODEL TRAINER")
        print("=" * 60)
        print(f"\nRecordings: {status['count']} ({status['duration_minutes']} min)")
        print(f"Quality: {status['quality']}")
        print(f"\nCommands:")
        print("  python train_model.py --check   Check recording status")
        print("  python train_model.py --train   Start training")
        print("  python train_model.py --test    Test the model")
        print("\nFirst, record phrases with: python record_voice.py")
        print("=" * 60)


if __name__ == "__main__":
    main()
