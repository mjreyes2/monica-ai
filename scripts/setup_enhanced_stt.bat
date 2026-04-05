@echo off
echo ========================================
echo Setting Up Enhanced STT Pipeline
echo ========================================

echo.
echo Step 1: Installing required Python packages...
python -m pip install --upgrade pip
python -m pip install torch torchaudio transformers datasets requests sentencepiece

echo.
echo Step 2: Installing pyctcdecode for KenLM integration...
pip install pyctcdecode

echo.
echo Step 3: Verifying KenLM installation...
python -c "import sys; sys.path.insert(0, r'C:\Monica\kenlm'); import kenlm; print('✅ KenLM is available')"

echo.
echo Step 4: Checking Ollama status...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Ollama is running
) else (
    echo ⚠️  Ollama is not running. Start it with: ollama serve
)

echo.
echo Step 5: Verifying Llama model...
curl -s -X POST http://localhost:11434/api/generate -d "{\"model\":\"llama3.2:1b\",\"prompt\":\"test\",\"stream\":false}" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo ✅ Llama 3.2 1B model is available
) else (
    echo ⚠️  Llama model not found. Pull it with: ollama pull llama3.2:1b
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Download or train a KenLM language model
echo 2. Test the pipeline with: python enhanced_stt_pipeline.py
echo.
pause
