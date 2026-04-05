# Monica AI

Your Intelligent AI Assistant with Voice and Vision capabilities.

## Project Structure

```
monica-ai/
├── main.py                    # Main entry point
├── setup.py                   # Package setup
├── requirements.txt           # Dependencies
├── .gitignore                 # Git ignore rules
│
├── src/                       # Source code
│   ├── core/                  # Core functionality
│   ├── services/              # Service modules
│   ├── models/                # AI models and training
│   ├── ui/                    # User interface components
│   └── utils/                 # Utility functions
│
├── config/                    # Configuration files
│   └── config.py              # Central configuration
│
├── data/                      # Data files
│   ├── training/              # Training data
│   ├── audio/                 # Audio files
│   └── knowledge/             # Knowledge base
│
├── tests/                     # Test files
├── scripts/                   # Setup and utility scripts
├── docs/                      # Documentation
└── logs/                      # Log files
```

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the environment: `.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Run the application: `python main.py`

## Features

- **Voice Recognition**: Advanced speech-to-text capabilities
- **Text-to-Speech**: Natural voice synthesis
- **Computer Vision**: Face detection, gesture recognition, emotion analysis
- **AI Services**: Integration with various AI models and APIs
- **AR/Hologram Support**: Augmented reality capabilities

## Development

The project follows a modular architecture with clear separation of concerns:

- `src/core/`: Main application logic and service orchestration
- `src/services/`: Individual service modules (STT, TTS, Vision, AI)
- `src/models/`: Machine learning models and training scripts
- `src/ui/`: User interface components
- `src/utils/`: Shared utility functions

## Testing

Run tests with: `pytest`

## Documentation

See the `docs/` directory for detailed documentation on setup, training, and architecture.