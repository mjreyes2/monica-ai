"""
NeMo ASR training using NeMo's exp_manager approach.
This bypasses the PyTorch Lightning compatibility issues.
"""

import nemo.collections.asr as nemo_asr
from nemo.core.config import hydra_runner
from omegaconf import OmegaConf
from pathlib import Path
import torch
import json

print("="*60)
print("MONICA VOICE TRAINING - NeMo ASR (Experimental Manager)")
print("="*60)

# Paths
recordings_dir = Path("voice_training/recordings/MJP")
manifest_file = recordings_dir / "manifest.json"
model_dir = Path("models/nemo_personal")
model_dir.mkdir(parents=True, exist_ok=True)

# Check recordings
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
model = nemo_asr.models.EncDecCTCModelBPE.from_pretrained("stt_en_conformer_ctc_small")

# Configure training data
print("\n[STEP 3/4] Configuring model...")
train_config = OmegaConf.create({
    "manifest_filepath": str(train_manifest),
    "sample_rate": 16000,
    "batch_size": 4,
    "shuffle": True,
    "num_workers": 4,
    "pin_memory": True,
    "trim_silence": False,
})

val_config = OmegaConf.create({
    "manifest_filepath": str(val_manifest),
    "sample_rate": 16000,
    "batch_size": 4,
    "shuffle": False,
    "num_workers": 4,
    "pin_memory": True,
})

model.setup_training_data(train_config)
model.setup_validation_data(val_config)

# Setup training with NeMo trainer
print("\n[STEP 4/4] Starting training...")
print("  Epochs: 50")
print("  Batch size: 4")
print("  Learning rate: 1e-4")
print("")

# Use NeMo's training approach
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint

checkpoint_callback = ModelCheckpoint(
    dirpath=str(model_dir / "checkpoints"),
    filename="monica_voice_{epoch:02d}",
    save_top_k=-1,
    every_n_epochs=10,
)

trainer = pl.Trainer(
    max_epochs=50,
    accelerator="gpu" if torch.cuda.is_available() else "cpu",
    devices=1,
    callbacks=[checkpoint_callback],
    enable_progress_bar=True,
    log_every_n_steps=5,
    check_val_every_n_epoch=5,
    logger=False,
)

# Critical: Set trainer BEFORE optimization
model.set_trainer(trainer)

# Setup optimizer
model.setup_optimization({
    "name": "adam",
    "lr": 1e-4,
    "weight_decay": 0.0001
})

# Train using NeMo's approach - call trainer's fit with the model directly
try:
    # The key is that NeMo models ARE LightningModules, but we need to ensure
    # the model is in the right state. Let's check inheritance first.
    from pytorch_lightning import LightningModule
    print(f"[DEBUG] Model is LightningModule: {isinstance(model, LightningModule)}")
    print(f"[DEBUG] Model type: {type(model)}")
    print(f"[DEBUG] Model MRO: {[c.__name__ for c in type(model).__mro__[:5]]}")

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
