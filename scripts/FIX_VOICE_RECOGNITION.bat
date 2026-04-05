@echo off
REM Fix Voice Recognition - Downgrade NumPy for SpeechBrain Compatibility
REM Issue: NumPy 2.2.6 is incompatible with SpeechBrain 1.0.3
REM Solution: Downgrade to NumPy 1.26.4

echo ================================================================================
echo FIXING VOICE RECOGNITION - NumPy Compatibility Fix
echo ================================================================================
echo.
echo Problem: NumPy 2.2.6 is incompatible with SpeechBrain
echo Solution: Downgrading to NumPy 1.26.4
echo.
echo This will fix the "Voice Recognition Failed" error in Monica GUI
echo.
echo ================================================================================
echo.

echo Downgrading NumPy from 2.2.6 to 1.26.4...
.venv\Scripts\python.exe -m pip install "numpy<2" --force-reinstall

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo SUCCESS! NumPy downgraded successfully
    echo ================================================================================
    echo.
    echo Verifying installation...
    .venv\Scripts\python.exe -c "import numpy; print('NumPy version:', numpy.__version__); import speechbrain; print('SpeechBrain version:', speechbrain.__version__); print('Voice recognition should now work!')"
    echo.
    echo ================================================================================
    echo NEXT STEPS:
    echo 1. Close this window
    echo 2. Restart Monica GUI
    echo 3. Click "Start Listening" - it should now work!
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo ERROR: Failed to downgrade NumPy
    echo ================================================================================
    echo Please try manually:
    echo .venv\Scripts\python.exe -m pip install "numpy<2"
)

echo.
pause
