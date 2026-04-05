@echo off
REM Launch Monica Voice Training GUI
REM This opens the recording interface with integrated training button

REM Isolate environment from system Python
set PYTHONPATH=
set PYTHONHOME=

REM Change to project root
cd /d "C:\Monica"

echo ================================================================================
echo MONICA VOICE TRAINING GUI
echo ================================================================================
echo.
echo Using Python: .venv\Scripts\python.exe (3.10.11)
echo PyTorch: 2.5.1+cu121
echo.
echo Starting voice training interface...
echo.
echo Features:
echo   - Record voice samples for training
echo   - Monitor recording progress
echo   - Start optimized training (22 epochs, FP16, memory-optimized)
echo   - View training results
echo.
echo ================================================================================
echo.

.venv\Scripts\python.exe launch_voice_training_gui.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ================================================================================
    echo ERROR: Failed to start voice training GUI
    echo ================================================================================
    pause
)
