# Post-Training Analysis Plan for Monica Voice Fine-Tuning

## Current Configuration
- **Epochs**: Changed from 50 to 22
- **Model**: wav2vec2-large-960h-lv60-self (Facebook)
- **Batch Size**: 1 (due to GPU memory constraints)
- **Learning Rates**:
  - Model (classifier): 0.5
  - Wav2vec2: 0.00005
- **Augmentation**: Currently disabled (commented out)

## Three-Step Post-Training Analysis

### 1. Review Training Behavior
After the 22-epoch training run completes, examine:

**a) Epochs Completed**
- Verify all 22 epochs ran successfully
- Check for any crashes or interruptions

**b) Validation Metrics Per Epoch**
- Look at WER (Word Error Rate) trajectory
- Look at CER (Character Error Rate) trajectory
- Identify when metrics started plateauing
- Check if metrics were still improving at epoch 22

**c) Best Checkpoint Selection**
- SpeechBrain's checkpointer saves based on minimum WER
- Verify which epoch had the best WER
- Location: `models/monica_finetuned/1986/save/`

**Key Files to Review**:
- `models/monica_finetuned/1986/train_log.txt` - Full training log with per-epoch metrics
- `models/monica_finetuned/1986/wer_test.txt` - Test set WER results

### 2. Tune Training Time / Early Stopping

Based on the training behavior observed:

**a) Adjust number_of_epochs**
- If WER plateaus before epoch 22: Reduce epochs
- If WER still improving at epoch 22: Consider increasing
- Typical plateau: 5-10 epochs with no improvement

**b) Add Early Stopping**
Currently NOT configured. Will add to `hparams_monica.yaml`:

```yaml
# Early stopping configuration (to be added)
train_logger: !new:speechbrain.utils.train_logger.FileTrainLogger
   save_file: !ref <train_log>

# Add early stopping to checkpointer
checkpointer: !new:speechbrain.utils.checkpoints.Checkpointer
   checkpoints_dir: !ref <save_folder>
   recoverables:
      wav2vec2: !ref <wav2vec2>
      model: !ref <model>
      scheduler_model: !ref <lr_annealing_model>
      scheduler_wav2vec: !ref <lr_annealing_wav2vec>
      counter: !ref <epoch_counter>
      tokenizer: !ref <label_encoder>
```

**Early Stopping Parameters to Consider**:
- `patience`: How many epochs to wait without improvement (default: 10)
- Based on WER plateau observation, may adjust to 5-7 epochs
- The NewBobScheduler already has `patient: 0` which reduces LR immediately

### 3. Add/Adjust Regularization & Augmentation

**a) Data Augmentation (Currently Disabled)**

The config has these augmentations commented out:
- Speed perturbation (95%, 100%, 105%)
- Frequency drop
- Time domain chunk dropping

**Decision Criteria**:
- If overfitting observed (train loss << val loss): Enable augmentation
- If underfitting (both losses high): Keep disabled or use minimal augmentation

**Minimal Augmentation to Try First**:
```yaml
# Light speed perturbation only
speed_perturb: !new:speechbrain.augment.time_domain.SpeedPerturb
   orig_freq: !ref <sample_rate>
   speeds: [97, 100, 103]  # Smaller variation

wav_augment: !new:speechbrain.augment.augmenter.Augmenter
   concat_original: True
   min_augmentations: 1
   max_augmentations: 1
   augment_prob: 0.5  # Only augment 50% of samples
   augmentations: [!ref <speed_perturb>]
```

**b) Regularization Check**

Current settings:
- Dropout: NOT explicitly set (check if VanillaNN has default)
- Weight decay: NOT set in optimizers
- Gradient clipping: NOT set

**To Add if Overfitting**:
```yaml
# Add dropout to DNN
enc: !new:speechbrain.lobes.models.VanillaNN.VanillaNN
   input_shape: [null, null, 1024]
   activation: !ref <activation>
   dnn_blocks: !ref <dnn_layers>
   dnn_neurons: !ref <dnn_neurons>
   dropout: 0.1  # Add this

# Add weight decay to optimizer
model_opt_class: !name:torch.optim.Adadelta
   lr: !ref <lr>
   rho: 0.95
   eps: 1.e-8
   weight_decay: 0.00001  # Add this

# Add gradient clipping
grad_clip: 5.0
```

## What to Do After Training Completes

1. **DO NOT** start a new training yet
2. Paste the last 30-50 lines of training log here
3. Especially look for:
   - Final epoch metrics (WER/CER)
   - "Model saved to:" line
   - Any errors or warnings
4. We'll analyze together and make targeted adjustments
5. Then integrate the best model into Monica's live STT

## Quick Commands for Analysis

```bash
# View last 50 lines of training log
tail -50 models/monica_finetuned/1986/train_log.txt

# Or on Windows
powershell -command "Get-Content models/monica_finetuned/1986/train_log.txt -Tail 50"

# Check which checkpoints exist
dir models\monica_finetuned\1986\save

# View test WER results
type models\monica_finetuned\1986\wer_test.txt
```

## Success Criteria

- **Good WER**: < 10% for custom voice with clean audio
- **Acceptable WER**: 10-20%
- **Needs work**: > 20%

For Monica's small dataset, we might see higher WER initially. The goal is:
1. Stable training without crashes
2. Clear learning curve (loss decreasing)
3. Validation WER improving over epochs
4. Best model selected and saved correctly
