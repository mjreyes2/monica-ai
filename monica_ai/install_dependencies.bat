@echo off
echo ========================================
echo   MONICA AI - Installing Dependencies
echo ========================================
echo.

cd /d "%~dp0"

echo Installing core dependencies...
pip install numpy opencv-python pillow pyaudio sounddevice

echo.
echo Installing speech recognition (Whisper)...
pip install openai-whisper torch torchaudio

echo.
echo Installing text-to-speech (Piper)...
pip install piper-tts

echo.
echo Installing AI backend (Ollama)...
pip install ollama

echo.
echo Installing additional dependencies...
pip install pygame requests python-dotenv pynput

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Make sure Ollama is running: ollama serve
echo 2. Pull an AI model: ollama pull llama3.2
echo 3. Run Monica AI: run_monica.bat
echo.
pause
