"""
Simple NeMo ASR training script that works around PyTorch Lightning compatibility issues.
Uses NeMo's native trainer interface.
"""

import nemo.collections.asr as nemo_asr
import pytorch_lightning as pl
from pathlib import Path
import torch

print("="*60)
print("MONICA VOICE TRAINING - NeMo ASR")
print("="*60)

# Paths
recordings_dir = Path("voice_training/recordings/MJP")
manifest_file = recordings_dir / "manifest.json"
model_dir = Path("models/nemo_personal")
model_dir.mkdir(parents=True, exist_ok=True)

# Check recordings
import json
count = 0
with open(manifest_file) as f:
    for line in f:
        if line.strip():
            count += 1

print(f"\n[INFO] Found {count} recordings")
print(f"[INFO] Manifest: {manifest_file}")
print(f"[INFO] Output: {model_dir}")

# Check GPU
if torch.cuda.is_available():
    print(f"[GPU] {torch.cuda.get_device_name(0)}")
    print(f"      Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
else:
    print("[WARNING] No GPU - training will be slow")

# Split data
print("\n[STEP 1/4] Preparing data split...")
entries = []
with open(manifest_file) as f:
    for line in f:
        if line.strip():
            entries.append(json.loads(line))

split_idx = int(len(entries) * 0.9)
train_entries = entries[:split_idx]
val_entries = entries[split_idx:]

train_manifest = recordings_dir / "train_manifest.json"
val_manifest = recordings_dir / "val_manifest.json"

with open(train_manifest, 'w') as f:
    for entry in train_entries:
        f.write(json.dumps(entry) + '\n')

with open(val_manifest, 'w') as f:
    for entry in val_entries:
        f.write(json.dumps(entry) + '\n')

print(f"  Training: {len(train_entries)} samples")
print(f"  Validation: {len(val_entries)} samples")

# Load model
print("\n[STEP 2/4] Loading NeMo model...")
model = nemo_asr.models.ASRModel.from_pretrained("stt_en_conformer_ctc_small")

# Configure for fine-tuning
print("\n[STEP 3/4] Configuring model...")
model.cfg.train_ds.manifest_filepath = str(train_manifest)
model.cfg.validation_ds.manifest_filepath = str(val_manifest)
model.cfg.train_ds.batch_size = 4  # Reduced for stability
model.cfg.validation_ds.batch_size = 4

model.setup_training_data(model.cfg.train_ds)
model.setup_validation_data(model.cfg.validation_ds)

# Training configuration
print("\n[STEP 4/4] Starting training...")
print("  Epochs: 50")
print("  Batch size: 4")
print("  Learning rate: 1e-4")
print("")

# Create trainer with NeMo configuration
from pytorch_lightning.callbacks import ModelCheckpoint

checkpoint_callback = ModelCheckpoint(
    dirpath=str(model_dir / "checkpoints"),
    filename="monica_voice_{epoch:02d}",
    save_top_k=-1,  # Save all checkpoints
    every_n_epochs=10,  # Save every 10 epochs
)

trainer = pl.Trainer(
    max_epochs=50,
    accelerator="gpu" if torch.cuda.is_available() else "cpu",
    devices=1,
    callbacks=[checkpoint_callback],
    enable_progress_bar=True,
    log_every_n_steps=5,
    check_val_every_n_epoch=5,
    logger=False,  # Disable default logger to avoid issues
)

# Set trainer and setup optimization
model.set_trainer(trainer)
model.setup_optimization({
    "name": "adam",
    "lr": 1e-4,
    "weight_decay": 0.0001
})

# Train!
try:
    trainer.fit(model)

    # Save final model
    final_model_path = model_dir / "monica_voice_model.nemo"
    model.save_to(str(final_model_path))

    print("\n" + "="*60)
    print("[SUCCESS] Training complete!")
    print(f"Model saved to: {final_model_path}")
    print("="*60)

except Exception as e:
    print(f"\n[ERROR] Training failed: {e}")
    import traceback
    traceback.print_exc()
