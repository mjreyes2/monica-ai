import wave
from pathlib import Path

# Cache the loaded PiperVoice instance to avoid reloading the model every call
_voice_cache = {}

def synthesize(text: str, model_path: Path, output_path: Path):
    """
    Synthesizes audio from text using the piper Python module.
    """
    from piper import PiperVoice

    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}")

    model_key = str(model_path)
    if model_key not in _voice_cache:
        _voice_cache[model_key] = PiperVoice.load(str(model_path))

    voice = _voice_cache[model_key]

    with wave.open(str(output_path), 'wb') as wav_file:
        voice.synthesize_wav(text, wav_file)
