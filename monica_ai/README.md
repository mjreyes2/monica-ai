# Monica AI

Your intelligent AI assistant with voice and vision capabilities.

## Features

- **Voice Interaction**: Natural speech recognition using OpenAI's Whisper
- **Wake Word Detection**: Say "Hey Monica" to activate
- **Natural Speech**: High-quality text-to-speech using Piper TTS
- **AI Conversation**: Powered by Ollama for intelligent responses
- **Camera Integration**: Live camera preview with face detection
- **OBS Integration**: Spout output for streaming
- **Modern UI**: Dark-themed, responsive interface

## Installation

### Prerequisites

- Python 3.8 or higher
- Windows 10/11 (for Spout support)
- NVIDIA GPU (recommended for faster speech recognition)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/monica-ai/monica.git
cd monica

# Install dependencies
pip install -r requirements.txt

# Run Monica AI
python main.py
```

### Full Installation (with all features)

```bash
pip install -e ".[full]"
```

## Usage

### Starting Monica AI

```bash
python main.py
```

Or if installed as a package:

```bash
monica-ai
```

### Voice Commands

1. **Manual Listening**: Click "🎤 Start Listening" to begin voice input
2. **Wake Word**: Click "👂 Wake Word" to enable "Hey Monica" detection
3. **Text Input**: Type in the text box and press Enter

### Settings

Click "⚙️ Settings" to configure:

- **Audio**: Input/output devices, Whisper model, language
- **Video**: Camera selection, resolution, Spout output
- **AI**: Model selection, temperature, TTS voice

### Debug Report

Click "📋 Debug Report" to generate a system diagnostic report.

## Configuration

Settings are saved to `config.json` in the application directory.

### Key Settings

```json
{
  "audio": {
    "sample_rate": 16000,
    "channels": 1
  },
  "stt": {
    "whisper_model": "base",
    "language": "en"
  },
  "wake_word": {
    "enabled": true,
    "word": "hey monica"
  },
  "ai": {
    "model": "llama3.2",
    "temperature": 0.7
  }
}
```

## Requirements

### Core Dependencies

- `numpy` - Numerical computing
- `opencv-python` - Camera capture
- `pillow` - Image processing
- `pyaudio` - Audio I/O
- `sounddevice` - Audio playback

### Optional Dependencies

- `torch` - GPU acceleration
- `openai-whisper` - Speech recognition
- `piper-tts` - Text-to-speech
- `ollama` - AI backend
- `SpoutGL` - OBS integration

## Troubleshooting

### No audio input

1. Check that your microphone is connected
2. Go to Settings > Audio and select the correct input device
3. Make sure no other application is using the microphone

### Speech recognition not working

1. Ensure Whisper is installed: `pip install openai-whisper`
2. Try a smaller model (tiny/base) if you have limited GPU memory
3. Check the debug report for errors

### Camera not showing

1. Check that your camera is connected
2. Go to Settings > Video and select the correct camera
3. Try closing other applications using the camera

### AI not responding

1. Ensure Ollama is running: `ollama serve`
2. Pull the model: `ollama pull llama3.2`
3. Check Settings > AI for the correct model name

## Architecture

```
monica_ai/
├── src/
│   ├── audio/           # Audio I/O, speech recognition, wake word
│   ├── tts/             # Text-to-speech synthesis
│   ├── vision/          # Camera capture, Spout output
│   ├── ai/              # Conversation management
│   ├── gui/             # User interface
│   ├── config/          # Configuration management
│   └── utils/           # Utilities and debugging
├── resources/
│   ├── voices/          # TTS voice models
│   ├── icons/           # Application icons
│   └── themes/          # UI themes
├── main.py              # Entry point
├── requirements.txt     # Dependencies
└── config.json          # User configuration
```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [Piper TTS](https://github.com/rhasspy/piper) - Text-to-speech
- [Ollama](https://ollama.ai/) - Local AI models
- [Spout](https://spout.zeal.co/) - Video sharing for OBS
