"""
Audio Input Enhancer for Monica AI
Implements automatic gain control and noise reduction
"""
import numpy as np
from collections import deque
import time

class AudioEnhancer:
    """Enhance audio input for better voice detection."""
    
    def __init__(self, sample_rate: int = 16000):
        """Initialize audio enhancer."""
        self.sample_rate = sample_rate
        
        # Automatic Gain Control (AGC)
        self.agc_enabled = True
        self.target_level = 0.02  # Target RMS level
        self.gain = 1.0
        self.gain_min = 0.5
        self.gain_max = 50.0  # Allow high gain for quiet inputs
        self.gain_smoothing = 0.95  # Smooth gain changes
        
        # Noise gate
        self.noise_gate_threshold = 0.0001
        
        # History for adaptive processing
        self.energy_history = deque(maxlen=100)
        self.last_energy = 0
        
        # Dynamic threshold adjustment
        self.dynamic_threshold = 0.0005
        self.calibrated = False
        
    def process_audio(self, audio_data: np.ndarray) -> tuple:
        """
        Process audio with AGC and enhancement.
        Returns (processed_audio, is_speech, energy_level)
        """
        # Ensure float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Step 1: Apply noise gate (remove very quiet noise)
        audio_data = self._apply_noise_gate(audio_data)
        
        # Step 2: Apply automatic gain control
        if self.agc_enabled:
            audio_data = self._apply_agc(audio_data)
        
        # Step 3: Calculate energy
        energy = np.sqrt(np.mean(audio_data ** 2))
        self.energy_history.append(energy)
        
        # Step 4: Dynamic threshold adjustment
        if not self.calibrated and len(self.energy_history) > 50:
            self._calibrate_threshold()
        
        # Step 5: Detect speech with hysteresis
        is_speech = self._detect_speech_with_hysteresis(energy)
        
        # Step 6: Additional boost for very quiet speech
        if is_speech and energy < 0.001:
            audio_data *= 2.0  # Extra boost for very quiet speech
        
        return audio_data, is_speech, energy
    
    def _apply_noise_gate(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply noise gate to remove very quiet background noise."""
        mask = np.abs(audio_data) > self.noise_gate_threshold
        return audio_data * mask
    
    def _apply_agc(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Apply Automatic Gain Control to normalize audio levels.
        Research shows AGC is critical for consistent voice detection.
        """
        # Calculate current RMS level
        rms = np.sqrt(np.mean(audio_data ** 2))
        
        if rms > 0:
            # Calculate desired gain to reach target level
            desired_gain = self.target_level / rms
            
            # Limit gain to prevent excessive amplification
            desired_gain = np.clip(desired_gain, self.gain_min, self.gain_max)
            
            # Smooth gain changes to prevent artifacts
            self.gain = self.gain * self.gain_smoothing + desired_gain * (1 - self.gain_smoothing)
            
            # Apply gain
            audio_data = audio_data * self.gain
            
            # Soft clipping to prevent distortion
            audio_data = np.tanh(audio_data * 0.7) / 0.7
            
            # Debug output
            if time.time() % 2 < 0.01:  # Log occasionally
                print(f"[AGC] Input RMS: {rms:.6f}, Gain: {self.gain:.2f}x, Output RMS: {np.sqrt(np.mean(audio_data**2)):.6f}")
        
        return audio_data
    
    def _detect_speech_with_hysteresis(self, energy: float) -> bool:
        """
        Detect speech with hysteresis to prevent flickering.
        Uses different thresholds for starting and stopping.
        """
        # Hysteresis thresholds
        start_threshold = self.dynamic_threshold
        stop_threshold = self.dynamic_threshold * 0.7
        
        # Was speaking in last frame?
        was_speaking = self.last_energy > stop_threshold
        
        # Determine current state
        if was_speaking:
            # Already speaking - use lower threshold to continue
            is_speaking = energy > stop_threshold
        else:
            # Not speaking - use higher threshold to start
            is_speaking = energy > start_threshold
        
        self.last_energy = energy
        return is_speaking
    
    def _calibrate_threshold(self):
        """
        Auto-calibrate threshold based on ambient noise.
        Research shows dynamic calibration improves accuracy.
        """
        if len(self.energy_history) < 50:
            return
        
        # Calculate noise floor (20th percentile)
        sorted_energy = sorted(self.energy_history)
        noise_floor = sorted_energy[int(len(sorted_energy) * 0.2)]
        
        # Set threshold above noise floor
        self.dynamic_threshold = max(noise_floor * 2, 0.0003)
        self.calibrated = True
        
        print(f"[CALIBRATION] Noise floor: {noise_floor:.6f}, Dynamic threshold: {self.dynamic_threshold:.6f}")
    
    def reset_calibration(self):
        """Reset calibration for new environment."""
        self.energy_history.clear()
        self.calibrated = False
        self.dynamic_threshold = 0.0005
        print("[CALIBRATION] Reset - will recalibrate")

class MicrophoneBooster:
    """Boost microphone input for better detection."""
    
    @staticmethod
    def boost_audio(audio_data: np.ndarray, boost_db: float = 20.0) -> np.ndarray:
        """
        Boost audio by specified decibels.
        20 dB = 10x amplification
        """
        # Convert dB to linear gain
        gain = 10 ** (boost_db / 20.0)
        
        # Apply gain
        boosted = audio_data * gain
        
        # Prevent clipping
        boosted = np.clip(boosted, -1.0, 1.0)
        
        return boosted
    
    @staticmethod
    def normalize_audio(audio_data: np.ndarray, target_peak: float = 0.9) -> np.ndarray:
        """Normalize audio to target peak level."""
        peak = np.max(np.abs(audio_data))
        
        if peak > 0:
            scale = target_peak / peak
            return audio_data * scale
        
        return audio_data

# Global enhancer instance
_audio_enhancer = None

def get_audio_enhancer(sample_rate: int = 16000):
    """Get or create audio enhancer."""
    global _audio_enhancer
    if _audio_enhancer is None:
        _audio_enhancer = AudioEnhancer(sample_rate)
        print("[AUDIO ENHANCER] Initialized with AGC and dynamic calibration")
    return _audio_enhancer
