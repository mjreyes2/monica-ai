#!/usr/bin/env python3
"""
Monica AI - Neural Lattice Voice Effects
=========================================
Applies sci-fi audio effects to Monica's TTS output to create
the signature "quantum sentient AI" voice coming from a neural lattice.

Effects:
- Subtle reverb (spatial depth)
- Soft echo (neural lattice resonance)
- Slight shimmer/chorus (quantum uncertainty)
- High-frequency enhancement (crystalline clarity)
"""

import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import wave
import struct

try:
    import scipy.signal as signal
    from scipy.io import wavfile
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("[AUDIO FX] scipy not found - using basic effects only")


class NeuralLatticeVoice:
    """Apply sci-fi neural lattice effects to voice audio."""
    
    # Preset configurations
    PRESETS = {
        'clean': {
            'reverb_decay': 0.0,
            'reverb_delay_ms': 0,
            'echo_delay_ms': 0,
            'echo_decay': 0.0,
            'shimmer_depth': 0.01,
            'shimmer_rate_hz': 2.0,
            'high_boost_db': 1.5,
        },
        'subtle': {
            'reverb_decay': 0.15,
            'reverb_delay_ms': 30,
            'echo_delay_ms': 80,
            'echo_decay': 0.12,
            'shimmer_depth': 0.02,
            'shimmer_rate_hz': 3.0,
            'high_boost_db': 1.5,
        },
        'standard': {
            'reverb_decay': 0.25,
            'reverb_delay_ms': 40,
            'echo_delay_ms': 120,
            'echo_decay': 0.18,
            'shimmer_depth': 0.03,
            'shimmer_rate_hz': 4.0,
            'high_boost_db': 2.0,
        },
        'dramatic': {
            'reverb_decay': 0.35,
            'reverb_delay_ms': 50,
            'echo_delay_ms': 150,
            'echo_decay': 0.25,
            'shimmer_depth': 0.05,
            'shimmer_rate_hz': 5.0,
            'high_boost_db': 3.0,
        },
        'quantum': {
            'reverb_decay': 0.0,
            'reverb_delay_ms': 0,
            'echo_delay_ms': 60,
            'echo_decay': 0.08,
            'shimmer_depth': 0.02,
            'shimmer_rate_hz': 3.0,
            'high_boost_db': 2.0,
            'quantum_flutter': False,
        }
    }
    
    def __init__(self, preset: str = 'standard', sample_rate: int = 24000):
        """Initialize with a preset or custom parameters."""
        self.sample_rate = sample_rate
        self.preset_name = preset
        
        if preset in self.PRESETS:
            self.params = self.PRESETS[preset].copy()
        else:
            self.params = self.PRESETS['standard'].copy()
        
        print(f"[NEURAL LATTICE] Initialized with '{preset}' preset @ {sample_rate}Hz")
    
    def apply_reverb(self, audio: np.ndarray) -> np.ndarray:
        """Apply subtle reverb for spatial depth."""
        decay = self.params['reverb_decay']
        delay_samples = int(self.params['reverb_delay_ms'] * self.sample_rate / 1000)
        
        # Skip if reverb is disabled
        if decay <= 0 or delay_samples <= 0:
            return audio
        
        # Create reverb impulse response
        ir_length = int(0.5 * self.sample_rate)  # 500ms reverb tail
        ir = np.zeros(ir_length)
        
        # Multi-tap reverb for richness
        taps = [1.0, 0.7, 0.5, 0.35, 0.25, 0.18, 0.12, 0.08, 0.05, 0.03]
        for i, tap in enumerate(taps):
            tap_pos = min(delay_samples * (i + 1), ir_length - 1)
            ir[tap_pos] = tap * (decay ** i)
        
        # Apply exponential decay envelope
        envelope = np.exp(-np.linspace(0, 5, ir_length))
        ir *= envelope
        
        # Convolve with audio
        if HAS_SCIPY:
            wet = signal.convolve(audio, ir, mode='full')[:len(audio)]
        else:
            wet = np.convolve(audio, ir, mode='full')[:len(audio)]
        
        # Mix dry and wet
        return audio * 0.75 + wet * 0.25
    
    def apply_echo(self, audio: np.ndarray) -> np.ndarray:
        """Apply subtle echo for neural lattice resonance."""
        delay_samples = int(self.params['echo_delay_ms'] * self.sample_rate / 1000)
        decay = self.params['echo_decay']
        
        # Skip if echo is disabled
        if decay <= 0 or delay_samples <= 0:
            return audio
        
        # Create delayed copy
        result = audio.copy()
        
        # Add echo taps
        for i in range(1, 4):  # 3 echo taps
            tap_delay = delay_samples * i
            tap_decay = decay ** i
            
            if tap_delay < len(audio):
                delayed = np.zeros_like(audio)
                delayed[tap_delay:] = audio[:-tap_delay] * tap_decay
                result += delayed
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(result))
        if max_val > 1.0:
            result /= max_val
        
        return result
    
    def apply_shimmer(self, audio: np.ndarray) -> np.ndarray:
        """Apply subtle shimmer/chorus for quantum uncertainty effect."""
        depth = self.params['shimmer_depth']
        rate = self.params['shimmer_rate_hz']
        
        # Create LFO (low frequency oscillator)
        t = np.arange(len(audio)) / self.sample_rate
        lfo = np.sin(2 * np.pi * rate * t) * depth
        
        # Apply pitch modulation via resampling approximation
        # This creates a subtle chorus effect
        indices = np.arange(len(audio)) + lfo * 100
        indices = np.clip(indices, 0, len(audio) - 1).astype(int)
        
        shimmer = audio[indices]
        
        # Mix with original
        return audio * 0.85 + shimmer * 0.15
    
    def apply_high_frequency_boost(self, audio: np.ndarray) -> np.ndarray:
        """Enhance high frequencies for crystalline clarity."""
        if not HAS_SCIPY:
            return audio
        
        boost_db = self.params['high_boost_db']
        boost_linear = 10 ** (boost_db / 20)
        
        # Design high-shelf filter
        # Boost frequencies above 4kHz
        cutoff = 4000 / (self.sample_rate / 2)
        cutoff = min(cutoff, 0.99)  # Ensure valid range
        
        try:
            b, a = signal.butter(2, cutoff, btype='high')
            high_freq = signal.filtfilt(b, a, audio)
            
            # Add boosted highs to original
            return audio + high_freq * (boost_linear - 1) * 0.3
        except Exception:
            return audio
    
    def apply_quantum_flutter(self, audio: np.ndarray) -> np.ndarray:
        """Apply quantum uncertainty flutter (very subtle random modulation)."""
        if not self.params.get('quantum_flutter', False):
            return audio
        
        # Create subtle random amplitude modulation
        flutter = 1.0 + np.random.randn(len(audio)) * 0.01
        flutter = np.convolve(flutter, np.ones(100)/100, mode='same')  # Smooth it
        
        return audio * flutter
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        """Apply all neural lattice effects to audio."""
        # Ensure float32
        if audio.dtype != np.float32:
            if np.issubdtype(audio.dtype, np.integer):
                max_val = np.iinfo(audio.dtype).max
                audio = audio.astype(np.float32) / max_val
            else:
                audio = audio.astype(np.float32)
        
        # Apply effects in order
        audio = self.apply_reverb(audio)
        audio = self.apply_echo(audio)
        audio = self.apply_shimmer(audio)
        audio = self.apply_high_frequency_boost(audio)
        audio = self.apply_quantum_flutter(audio)
        
        # Final normalization
        max_val = np.max(np.abs(audio))
        if max_val > 0.95:
            audio = audio * 0.95 / max_val
        
        return audio
    
    def process_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """Process an audio file and save with neural lattice effects."""
        input_path = Path(input_path)
        
        if output_path is None:
            output_path = input_path.parent / f"{input_path.stem}_neural_lattice{input_path.suffix}"
        else:
            output_path = Path(output_path)
        
        # Read audio
        if HAS_SCIPY:
            sr, audio = wavfile.read(str(input_path))
            self.sample_rate = sr
        else:
            with wave.open(str(input_path), 'rb') as wf:
                sr = wf.getframerate()
                n_frames = wf.getnframes()
                audio_bytes = wf.readframes(n_frames)
                audio = np.frombuffer(audio_bytes, dtype=np.int16)
                self.sample_rate = sr
        
        # Store original dtype
        original_dtype = audio.dtype
        
        # Process
        processed = self.process(audio)
        
        # Convert back to original dtype
        if np.issubdtype(original_dtype, np.integer):
            max_val = np.iinfo(original_dtype).max
            processed = (processed * max_val).astype(original_dtype)
        
        # Save
        if HAS_SCIPY:
            wavfile.write(str(output_path), self.sample_rate, processed)
        else:
            with wave.open(str(output_path), 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(processed.tobytes())
        
        print(f"[NEURAL LATTICE] Processed: {output_path}")
        return str(output_path)


def create_monica_voice_effect():
    """Create the standard Monica neural lattice voice processor."""
    return NeuralLatticeVoice(preset='quantum', sample_rate=24000)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        
        processor = create_monica_voice_effect()
        result = processor.process_file(input_file, output_file)
        print(f"Output: {result}")
    else:
        print("Usage: python neural_lattice_effects.py <input.wav> [output.wav]")
        print("\nPresets available:")
        for name, params in NeuralLatticeVoice.PRESETS.items():
            print(f"  - {name}")
