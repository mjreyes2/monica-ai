# Monica AI - Complete Setup Guide

## Step 1: Install Ollama and Model

You mentioned you've installed Ollama. Let's verify and set up the model:

### Windows Installation

1. **Download Ollama**:
   - Visit: https://ollama.com/download
   - Download for Windows
   - Run the installer

2. **Install the Model**:
   Open Command Prompt or PowerShell and run:
   ```bash
   ollama pull llama3.2
   ```

   Or for more advanced reasoning:
   ```bash
   ollama pull llama3.2:latest
   ```

3. **Verify Installation**:
   ```bash
   ollama list
   ```

   You should see `llama3.2` in the list.

4. **Test Ollama**:
   ```bash
   ollama run llama3.2 "Hello, what is your name?"
   ```

### Keep Ollama Running

Ollama needs to be running in the background. On Windows, it should start automatically. If not:

```bash
# Start Ollama service
ollama serve
```

Keep this terminal open, or run it as a background service.

## Step 2: Install Python Dependencies

Monica needs these packages:

```bash
# Navigate to project directory
cd C:\Users\mxz\StreamAnimateFog

# Install all requirements
pip install ollama requests duckduckgo-search opencv-python numpy mediapipe pyttsx3 SpeechRecognition pyaudio pygame

# Optional but recommended
pip install beautifulsoup4 lxml pyautogui pillow
```

## Step 3: Test Monica's Intelligence

Run this test:

```bash
python test_monica_intelligence.py
```

(We'll create this file in a moment)

## Step 4: Launch Monica

```bash
# With avatar
python monica_avatar_integration.py

# Or complete demo
python monica_complete_demo.py

# Or main system
python monica_ultimate.py
```

## Common Issues

### Ollama Not Found
- Make sure Ollama is installed and in your PATH
- Restart your terminal after installation
- On Windows, you may need to restart your computer

### Model Download Fails
- Check your internet connection
- Try a smaller model first: `ollama pull llama3.2:1b`
- Then upgrade: `ollama pull llama3.2`

### Import Errors
- Make sure you're in the correct Python environment
- Activate virtual environment if you have one:
  ```bash
  .venv\Scripts\activate
  ```

### Port Already in Use
- Ollama runs on port 11434 by default
- Make sure nothing else is using that port
- Or change the port in environment variables

## What Monica Can Do Now

With Ollama installed, Monica gains:
- ✅ AI-powered concept extraction
- ✅ Intelligent summarization
- ✅ Learning from text, PDFs, audio, video
- ✅ Critical thinking and reasoning
- ✅ Web research capabilities
- ✅ Code generation
- ✅ Problem-solving
- ✅ Memory and context retention

## Next: Advanced Intelligence Features

See `MONICA_INTELLIGENCE_GUIDE.md` for details on Monica's reasoning capabilities.
