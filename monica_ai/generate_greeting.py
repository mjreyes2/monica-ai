#!/usr/bin/env python3
"""
Generate pre-recorded greeting audio for Monica AI.
This creates a WAV file that can be played instantly on "Monica initialize".
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.config.settings import config
from src.tts.tts_manager import TTSManager
import numpy as np
import wave

def generate_greeting():
    """Generate the greeting audio file."""
    print("Initializing TTS Manager...")
    tts = TTSManager(config)
    
    # The greeting text
    greeting = "Hello MJP! I'm fully operational and ready to assist you."
    
    print(f"Generating audio for: '{greeting}'")
    
    # Generate audio
    audio = tts._synthesize(greeting)
    
    if audio is None:
        print("ERROR: Failed to generate audio!")
        return False
    
    # Save as WAV file
    output_path = Path(__file__).parent / "resources" / "audio" / "greeting.wav"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Normalize audio to int16
    audio_int16 = (audio * 32767).astype(np.int16)
    
    # Write WAV file
    sample_rate = tts.sample_rate
    with wave.open(str(output_path), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())
    
    print(f"✅ Greeting saved to: {output_path}")
    print(f"   Duration: {len(audio) / sample_rate:.2f} seconds")
    print(f"   Sample rate: {sample_rate} Hz")
    
    # Also generate the startup sound + robotic voice + greeting combo
    print("\nGenerating full startup sequence...")
    
    # 1. Startup sound
    startup_sound = tts.generate_scifi_startup_sound()
    
    # 2. Robotic "Monica initializing"
    robotic = tts.generate_robotic_voice("Monica initializing")
    
    # 3. Greeting
    greeting_audio = audio
    
    # Combine all with small gaps
    gap = np.zeros(int(sample_rate * 0.3), dtype=np.float32)  # 0.3 second gap
    
    full_sequence = np.concatenate([
        startup_sound,
        gap,
        robotic if robotic is not None else np.array([], dtype=np.float32),
        gap,
        greeting_audio
    ])
    
    # Save full sequence
    full_path = Path(__file__).parent / "resources" / "audio" / "startup_sequence.wav"
    full_int16 = (full_sequence * 32767).astype(np.int16)
    
    with wave.open(str(full_path), 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(full_int16.tobytes())
    
    print(f"✅ Full startup sequence saved to: {full_path}")
    print(f"   Duration: {len(full_sequence) / sample_rate:.2f} seconds")
    
    return True

if __name__ == "__main__":
    success = generate_greeting()
    sys.exit(0 if success else 1)
