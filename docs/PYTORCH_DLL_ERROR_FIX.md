# PyTorch DLL Entry Point Error - Complete Fix Guide

## Error Details

**Full Error**:
```
The procedure entry point ?dtype@tensoroptions@c10@@QEBA?AU12@V?$optional@W4ScalarType@c10@@@2@@Z
could not be located in the dynamic library C:\Users\mxz\local\programs\python
```

**What it means**: PyTorch's core library (c10.dll) has a version mismatch or corruption

## Root Cause Analysis

### Possible Causes (from research):

1. **Version Mismatch** between PyTorch packages
   - Common after upgrading/downgrading packages
   - Source: [PyTorch Forums - Procedure Entry Point](https://discuss.pytorch.org/t/the-procedure-entry-point/77890)

2. **Corrupted Installation**
   - DLLs not properly compiled or mixed versions
   - Source: [PyTorch DLL Issues](https://discuss.pytorch.org/t/filenotfounderror-could-not-find-module-c10-dll/88422)

3. **Multiple Python Installations**
   - System loading wrong DLLs from PATH
   - Detected: Python 3.10 (venv) + Python 3.11 (system)

4. **NumPy Downgrade Side Effect**
   - Downgrading NumPy 2.2.6 → 1.26.4 may have triggered package rebuilds
   - Some packages compiled for NumPy 2.x now incompatible

## Current System State

✅ **Versions are correct**:
- torch: 2.5.1+cu121
- torchvision: 0.20.1+cu121
- torchaudio: 2.5.1+cu121
- These versions are compatible! (Source: [PyTorch Previous Versions](https://pytorch.org/get-started/previous-versions/))

❌ **Issue**: DLL corruption or PATH conflict despite correct versions

## Solution 1: Clean PyTorch Reinstall (Recommended)

### Quick Fix
```bash
# Double-click this file:
FIX_PYTORCH_DLL.bat
```

### Manual Steps
```bash
# 1. Uninstall PyTorch ecosystem
.venv\Scripts\python.exe -m pip uninstall -y torch torchvision torchaudio

# 2. Clear cache
.venv\Scripts\python.exe -m pip cache purge

# 3. Reinstall with matching versions
.venv\Scripts\python.exe -m pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
```

## Solution 2: Use CPU-Only PyTorch (Workaround)

If CUDA version is causing issues:

```bash
.venv\Scripts\python.exe -m pip uninstall -y torch torchvision torchaudio
.venv\Scripts\python.exe -m pip install torch torchvision torchaudio
```

Note: This removes CUDA support (GPU training) but will fix DLL issues.

## Solution 3: Downgrade to PyTorch 2.4.1

Sometimes older versions are more stable:

```bash
.venv\Scripts\python.exe -m pip uninstall -y torch torchvision torchaudio
.venv\Scripts\python.exe -m pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --index-url https://download.pytorch.org/whl/cu121
```

## Solution 4: Check PATH Conflicts

### Detected Multiple Python Installations:
- Python 3.11: `C:\Users\mxz\AppData\Local\Programs\Python\Python311\`
- Virtual env: `.venv\Scripts\python.exe`

### Fix PATH Issues:
1. Always use full path to venv Python: `.venv\Scripts\python.exe`
2. Never run `python` directly - might use wrong version
3. Batch files should use `.venv\Scripts\python.exe` explicitly

## Testing After Fix

### Test 1: Import PyTorch
```bash
.venv\Scripts\python.exe -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

**Expected Output**:
```
PyTorch: 2.5.1+cu121
CUDA: True
```

### Test 2: Import All Packages
```bash
.venv\Scripts\python.exe -c "import torch, torchvision, torchaudio; print('All imports successful!')"
```

### Test 3: Test SpeechBrain
```bash
.venv\Scripts\python.exe -c "import speechbrain; print('SpeechBrain OK')"
```

### Test 4: Launch Voice Training GUI
```bash
START_VOICE_TRAINING.bat
```

Should launch without DLL errors.

## If Error Persists

### Advanced Debugging

**Check which DLLs are loaded**:
```bash
.venv\Scripts\python.exe -c "import torch; import os; print('torch path:', torch.__file__); print('DLL dir:', os.path.dirname(torch.__file__))"
```

**Check for conflicting packages**:
```bash
.venv\Scripts\python.exe -m pip check
```

**Full nuclear option** (last resort):
```bash
# Delete entire virtual environment
rmdir /s /q .venv

# Recreate from scratch
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Known Working Configuration

After fix, your system should have:
- ✅ Python: 3.10.x (in venv)
- ✅ NumPy: 1.26.4 (for SpeechBrain compatibility)
- ✅ PyTorch: 2.5.1+cu121
- ✅ torchvision: 0.20.1+cu121
- ✅ torchaudio: 2.5.1+cu121
- ✅ SpeechBrain: 1.0.3
- ✅ PyAudio: 0.2.14

## Sources

### Research Sources:
- [PyTorch Forums - DLL Entry Point Errors](https://discuss.pytorch.org/t/the-procedure-entry-point/77890)
- [PyTorch Forums - c10.dll Issues](https://discuss.pytorch.org/t/filenotfounderror-could-not-find-module-c10-dll/88422)
- [PyTorch Forums - c10_cuda.dll Loading Error](https://discuss.pytorch.org/t/error-loading-c10-cuda-dll-or-one-of-its-dependencies/208539)
- [PyTorch Previous Versions](https://pytorch.org/get-started/previous-versions/)
- [PyTorch Compatibility Matrix](https://github.com/eminsafa/pytorch-cuda-compatibility)
- [Stable Diffusion WebUI xFormers Issue](https://github.com/AUTOMATIC1111/stable-diffusion-webui/issues/15444)

## Quick Command Reference

```bash
# Fix voice recognition (NumPy)
FIX_VOICE_RECOGNITION.bat

# Fix PyTorch DLL error
FIX_PYTORCH_DLL.bat

# Start voice training
START_VOICE_TRAINING.bat

# Monitor GPU during training
.venv\Scripts\python.exe monitor_gpu_memory.py

# View training log
powershell -command "Get-Content models\monica_finetuned\1986\train_log.txt -Tail 50"
```

## Summary

The DLL error is likely caused by:
1. ✅ Corrupted PyTorch installation (most likely)
2. ✅ NumPy downgrade side effects
3. ✅ Multiple Python installations in PATH

**Recommended fix**: Run `FIX_PYTORCH_DLL.bat` for clean reinstall.

After fix:
- ✅ Voice recognition will work
- ✅ Voice training GUI will launch
- ✅ GPU training will be available
- ✅ No more DLL errors!
