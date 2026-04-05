# CUDA Memory Optimization Summary

## Problem
Training was experiencing CUDA Out-of-Memory (OOM) crashes on 8GB VRAM GPU.

## Solutions Implemented

### 1. Mixed Precision Training (FP16)
**File**: `hparams_monica.yaml:40`
```yaml
precision: fp16  # Changed from fp32
```
**Benefit**: Reduces memory usage by ~50% by using 16-bit floats instead of 32-bit
**Implementation**: Uses PyTorch's Automatic Mixed Precision (AMP) with gradient scaler

### 2. Gradient Accumulation
**File**: `hparams_monica.yaml:48`
```yaml
grad_accumulation_factor: 4
```
**Benefit**: Simulates batch_size=4 while keeping actual batch_size=1
- Only updates weights every 4 steps
- Accumulates gradients without storing extra batches in memory
- Gives better gradient estimates than batch_size=1

### 3. Gradient Checkpointing
**File**: `hparams_monica.yaml:96`
```yaml
gradient_checkpointing: True
```
**Benefit**: Trades computation for memory
- Doesn't store all intermediate activations
- Recomputes them during backward pass
- Can save 30-50% memory on large models like wav2vec2

### 4. Gradient Clipping
**File**: `hparams_monica.yaml:51`
```yaml
grad_clip: 5.0
```
**Benefit**: Prevents exploding gradients and stabilizes training
- Especially important with fp16 and gradient accumulation

### 5. CUDA Memory Configuration
**File**: `train_monica.py:28-29`
```python
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128,expandable_segments:True'
```
**Benefit**:
- `max_split_size_mb:128`: Limits memory fragmentation
- `expandable_segments:True`: Allows better memory allocation

### 6. Aggressive Memory Clearing
**File**: `train_monica.py:137-143`
```python
torch.cuda.empty_cache()
gc.collect()
```
**Benefit**: Clears unused memory after each training step
- Prevents gradual memory accumulation
- Helps with memory fragmentation

### 7. Frozen Feature Extractor
**File**: `hparams_monica.yaml:94`
```yaml
freeze_feature_extractor: True
```
**Benefit**: Doesn't compute gradients for wav2vec2's CNN layers
- Saves ~20% memory during backprop
- Focuses fine-tuning on transformer layers

### 8. Custom fit_batch with AMP Support
**File**: `train_monica.py:236-293`
- Implements proper gradient accumulation
- Uses torch.cuda.amp.autocast() for fp16
- Uses GradScaler for stable fp16 training
- Only steps optimizer every N batches

## Memory Usage Estimation

### Before Optimizations (fp32, batch_size=1)
- Model: ~3.5 GB
- Activations: ~2.5 GB
- Gradients: ~1.5 GB
- **Total: ~7.5 GB** (barely fits, unstable)

### After Optimizations (fp16, gradient checkpointing)
- Model: ~1.8 GB (fp16)
- Activations: ~0.8 GB (checkpointing)
- Gradients: ~0.8 GB (fp16)
- Optimizer states: ~1.0 GB
- **Total: ~4.4 GB** (comfortable margin)

## Expected Impact

**Memory Savings**: ~40-50% reduction
- FP16: 50% reduction in model/gradients
- Gradient checkpointing: 30-50% reduction in activations
- Combined with better memory management

**Training Stability**: Much improved
- Gradient clipping prevents spikes
- Aggressive cache clearing prevents fragmentation
- Gradient accumulation smooths out updates

**Training Speed**: Slightly slower
- Gradient checkpointing adds ~20% compute overhead (recomputes activations)
- But enables training to complete without crashes
- Overall: 10-20% slower per epoch, but no crashes = success!

## Monitoring During Training

Watch for these in the logs:
```
epoch: 1, lr_model: 0.5, lr_wav2vec: 5e-05
train loss: X.XXX
valid loss: X.XXX, valid WER: XX.XX, valid CER: XX.XX
```

**Good signs**:
- Loss decreasing steadily
- No OOM errors
- WER/CER improving

**Warning signs**:
- `CUDA out of memory` - May need to reduce grad_accumulation_factor
- Loss = NaN - Reduce learning rate or grad_clip value
- Very slow (<1 it/s) - This is expected with checkpointing

## Emergency Fallback Options

If OOM still occurs:

1. **Reduce gradient accumulation**:
   ```yaml
   grad_accumulation_factor: 2  # Instead of 4
   ```

2. **Freeze wav2vec2 completely**:
   ```yaml
   freeze_wav2vec: True
   ```

3. **Reduce DNN size**:
   ```yaml
   dnn_neurons: 256  # Instead of 512
   ```

4. **Use a smaller wav2vec2 model**:
   ```yaml
   wav2vec2_hub: facebook/wav2vec2-base-960h
   ```

## How to Start Training

```bash
.venv\Scripts\python.exe train_monica.py hparams_monica.yaml
```

The training will:
1. Load wav2vec2-large-960h-lv60-self (~1.2GB download first time)
2. Initialize with fp16 mixed precision
3. Train for 22 epochs with gradient accumulation
4. Save best checkpoint based on validation WER
5. Output logs to `models/monica_finetuned/1986/train_log.txt`

## Post-Training

After successful completion:
1. Check `POST_TRAINING_ANALYSIS_PLAN.md` for next steps
2. Review final WER/CER metrics
3. Test best checkpoint in Monica's STT system
4. Optionally tune and retrain with adjustments
