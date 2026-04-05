@echo off
echo ========================================
echo        MONICA AI - Starting...
echo ========================================
echo.

cd /d "%~dp0\.."

REM ── Virtual environment (local path, not OneDrive) ──
set "VENV=C:\Users\Marvi\monica_venv"
if exist "%VENV%\Scripts\activate.bat" (
    call "%VENV%\Scripts\activate.bat"
) else (
    echo ERROR: Virtual environment not found at %VENV%
    echo Run: python -m venv "%VENV%"  then install dependencies.
    pause
    exit /b 1
)

REM ── Torch DLL fix (required for CPU-only torch on Windows) ──
set "PATH=%VENV%\Lib\site-packages\torch\lib;%PATH%"

cd /d "%~dp0"

REM Run Monica AI
python main.py %*

if errorlevel 1 (
    echo.
    echo Monica AI exited with an error.
    pause
)
