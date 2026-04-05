@echo off
REM Fix PyTorch DLL Entry Point Error
REM Error: "procedure entry point ?dtype@tensoroptions@c10@@QEBA..."
REM Solution: Clean reinstall of PyTorch ecosystem

echo ================================================================================
echo FIXING PYTORCH DLL ENTRY POINT ERROR
echo ================================================================================
echo.
echo Problem: PyTorch DLL compatibility issue
echo Solution: Clean reinstall of torch/torchvision/torchaudio
echo.
echo This will fix the "procedure entry point" error
echo.
echo ================================================================================
echo.

echo Step 1: Uninstalling current PyTorch installation...
.venv\Scripts\python.exe -m pip uninstall -y torch torchvision torchaudio

echo.
echo Step 2: Cleaning pip cache...
.venv\Scripts\python.exe -m pip cache purge

echo.
echo Step 3: Reinstalling PyTorch 2.5.1 with CUDA 12.1 support...
echo (This may take 2-3 minutes...)
.venv\Scripts\python.exe -m pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo SUCCESS! PyTorch reinstalled successfully
    echo ================================================================================
    echo.
    echo Verifying installation...
    .venv\Scripts\python.exe -c "import torch; print('PyTorch:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); import torchvision; print('torchvision:', torchvision.__version__); import torchaudio; print('torchaudio:', torchaudio.__version__); print('\nPyTorch ecosystem working correctly!')"
    echo.
    echo ================================================================================
    echo NEXT STEPS:
    echo 1. Close this window
    echo 2. Try launching Monica GUI or voice training again
    echo 3. The DLL error should be fixed!
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo ERROR: Failed to reinstall PyTorch
    echo ================================================================================
    echo Please check your internet connection and try again.
)

echo.
pause
