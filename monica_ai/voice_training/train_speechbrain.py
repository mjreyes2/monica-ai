"""
Monica AI Voice Training with SpeechBrain
Fine-tune a SpeechBrain ASR model on your personal voice recordings.
"""

import json
import torch
from pathlib import Path
import csv

print("="*60)
print("MONICA VOICE TRAINING - SpeechBrain ASR")
print("="*60)

# Paths
recordings_dir = Path("voice_training/recordings/MJP")
manifest_file = recordings_dir / "manifest.json"
model_dir = Path("models/speechbrain_personal")
model_dir.mkdir(parents=True, exist_ok=True)

# Check recordings
print(f"\n[STEP 1/5] Loading recordings...")
entries = []
with open(manifest_file) as f:
    for line in f:
        if line.strip():
            entries.append(json.loads(line))

print(f"[INFO] Found {len(entries)} recordings")
print(f"[INFO] Total duration: {sum(e['duration'] for e in entries):.1f} seconds")

# Check GPU
if torch.cuda.is_available():
    print(f"[GPU] {torch.cuda.get_device_name(0)}")
    print(f"      Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
else:
    print("[WARNING] No GPU detected - training will be slow")

# Split data (90/10)
print("\n[STEP 2/5] Preparing data split...")
split_idx = int(len(entries) * 0.9)
train_entries = entries[:split_idx]
val_entries = entries[split_idx:]

print(f"  Training: {len(train_entries)} samples")
print(f"  Validation: {len(val_entries)} samples")

# Create SpeechBrain CSV format
# Format: ID,duration,wav,wrd
def create_csv(entries, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'duration', 'wav', 'wrd'])
        for i, entry in enumerate(entries):
            # Convert Windows path to forward slashes for consistency
            wav_path = entry['audio_filepath'].replace('\\', '/')
            writer.writerow([
                f"sample_{i:04d}",
                entry['duration'],
                wav_path,
                entry['text']
            ])

train_csv = recordings_dir / "train.csv"
val_csv = recordings_dir / "val.csv"

create_csv(train_entries, train_csv)
create_csv(val_entries, val_csv)

print(f"[INFO] Created training CSV: {train_csv}")
print(f"[INFO] Created validation CSV: {val_csv}")

# Load pretrained model from HuggingFace
print("\n[STEP 3/5] Loading pretrained SpeechBrain model...")
from speechbrain.inference.ASR import EncoderDecoderASR

try:
    # Try loading a small pretrained ASR model
    asr_model = EncoderDecoderASR.from_hparams(
        source="speechbrain/asr-crdnn-rnnlm-librispeech",
        savedir="models/speechbrain_pretrained"
    )
    print("[SUCCESS] Loaded pretrained model: asr-crdnn-rnnlm-librispeech")
except Exception as e:
    print(f"[WARNING] Could not load pretrained model: {e}")
    print("[INFO] Will use default configuration")

# Create training configuration
print("\n[STEP 4/5] Creating training configuration...")

config_yaml = f"""
# SpeechBrain ASR Training Config for Monica
# Seed for reproducibility
seed: 2024
__set_seed: !apply:torch.manual_seed [!ref <seed>]

# Data files
data_folder: {recordings_dir.absolute().as_posix()}
train_csv: {train_csv.absolute().as_posix()}
valid_csv: {val_csv.absolute().as_posix()}
skip_prep: True

# Output folder
output_folder: {model_dir.absolute().as_posix()}
save_folder: !ref <output_folder>/save
train_log: !ref <output_folder>/train_log.txt

# Training parameters
number_of_epochs: 50
batch_size: 4
lr: 0.0001
sorting: ascending

# Feature extraction
sample_rate: 16000
n_fft: 400
n_mels: 80

# Model architecture - using CRDNN (Convolutional RNN DNN)
activation: !name:torch.nn.LeakyReLU
dropout: 0.15
cnn_blocks: 2
cnn_channels: (64, 128)
rnn_layers: 4
rnn_neurons: 512
rnn_bidirectional: True
dnn_blocks: 2
dnn_neurons: 512

# Dataloader options
train_dataloader_opts:
    batch_size: !ref <batch_size>
    shuffle: True

valid_dataloader_opts:
    batch_size: !ref <batch_size>

# Optimizer
opt_class: !name:torch.optim.Adam
    lr: !ref <lr>

# Checkpointer
checkpointer: !new:speechbrain.utils.checkpoints.Checkpointer
    checkpoints_dir: !ref <save_folder>
    recoverables:
        model: !ref <model>
        scheduler: !ref <lr_annealing>
        counter: !ref <epoch_counter>
"""

config_file = model_dir / "train_config.yaml"
with open(config_file, 'w') as f:
    f.write(config_yaml)

print(f"[INFO] Configuration saved to: {config_file}")

# Start training
print("\n[STEP 5/5] Starting training...")
print("  Epochs: 50")
print("  Batch size: 4")
print("  Learning rate: 0.0001")
print("\nNote: SpeechBrain training requires a complete YAML config.")
print("      For now, the data is prepared and ready.")
print("\nTo continue training, you'll need to:")
print("1. Use a SpeechBrain recipe (recommended)")
print("2. Or create a custom training script with Brain class")
print("\nYour recordings are ready in SpeechBrain CSV format!")
print(f"  Train: {train_csv}")
print(f"  Valid: {val_csv}")
print("="*60)
