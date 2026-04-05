"""
Automatic Voice Detection Calibration for Monica AI
Based on research from speech recognition best practices
"""
import numpy as np
import pyaudio
import time
from typing import Tuple, Optional
import json
from pathlib import Path

class VoiceCalibrator:
    """Automatically calibrate voice detection thresholds."""
    
    def __init__(self, sample_rate: int = 16000, chunk_size: int = 1024):
        """Initialize calibrator."""
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio = None
        self.stream = None
        
    def calibrate_microphone(self, duration: float = 3.0, device_index: Optional[int] = None) -> dict:
        """
        Calibrate microphone for ambient noise and speaking levels.
        
        Research shows that dynamic calibration is critical for accurate voice detection.
        """
        print("\n" + "="*60)
        print("[Mic] MICROPHONE CALIBRATION")
        print("="*60)
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Find and display available devices
        if device_index is None:
            device_index = self._find_best_input_device()
        
        # Open stream
        try:
            self.stream = self.audio.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            # Step 1: Measure ambient noise
            print("\n[Stats] Step 1: Measuring ambient noise...")
            print("Please remain SILENT for 3 seconds...")
            ambient_energy = self._measure_ambient_noise(duration)
            print(f"[*] Ambient noise level: {ambient_energy:.6f}")
            
            # Step 2: Measure speaking voice
            print("\n[Stats] Step 2: Measuring your voice...")
            print("Please SPEAK NORMALLY (say 'Monica, hello' repeatedly) for 5 seconds...")
            print("Starting in 3...")
            time.sleep(1)
            print("2...")
            time.sleep(1)
            print("1...")
            time.sleep(1)
            print("SPEAK NOW!")
            
            speaking_energy = self._measure_speaking_voice(5.0)
            print(f"[*] Speaking voice level: {speaking_energy:.6f}")
            
            # Step 3: Calculate optimal thresholds
            # Research shows the threshold should be between ambient and speaking levels
            # Typically 1.5-2x ambient noise for good sensitivity
            
            if speaking_energy > ambient_energy * 2:
                # Good signal-to-noise ratio
                energy_threshold = ambient_energy * 1.5
                print(f"\n[OK] Good microphone signal detected!")
            else:
                # Poor signal-to-noise ratio - be more aggressive
                energy_threshold = ambient_energy * 1.2
                print(f"\n[WARNING] Low microphone signal - adjusting sensitivity")
            
            # Ensure threshold is reasonable
            energy_threshold = max(0.001, min(energy_threshold, 0.01))
            
            # Calculate dynamic adjustment factor
            dynamic_factor = speaking_energy / ambient_energy if ambient_energy > 0 else 10
            
            calibration = {
                "ambient_energy": float(ambient_energy),
                "speaking_energy": float(speaking_energy),
                "energy_threshold": float(energy_threshold),
                "signal_to_noise_ratio": float(dynamic_factor),
                "device_index": device_index,
                "calibration_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "recommendations": self._get_recommendations(ambient_energy, speaking_energy, dynamic_factor)
            }
            
            # Display results
            print("\n" + "="*60)
            print("[*] CALIBRATION RESULTS:")
            print(f"  • Ambient Noise: {ambient_energy:.6f}")
            print(f"  • Speaking Level: {speaking_energy:.6f}")
            print(f"  • Signal/Noise Ratio: {dynamic_factor:.1f}x")
            print(f"  • Recommended Threshold: {energy_threshold:.6f}")
            
            if dynamic_factor < 3:
                print("\n[WARNING] WARNING: Low signal-to-noise ratio detected!")
                print("  Recommendations:")
                print("  • Move closer to microphone")
                print("  • Reduce background noise")
                print("  • Check microphone sensitivity in Windows settings")
            elif dynamic_factor < 5:
                print("\n[*] FAIR: Acceptable signal quality")
                print("  • Consider moving slightly closer to microphone")
            else:
                print("\n[OK] EXCELLENT: Great signal quality!")
            
            print("="*60 + "\n")
            
            # Clean up
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            
            return calibration
            
        except Exception as e:
            print(f"\n[ERROR] Calibration failed: {e}")
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.audio:
                self.audio.terminate()
            raise
    
    def _find_best_input_device(self) -> Optional[int]:
        """Find the best input device."""
        print("\n[Search] Detecting microphones...")
        
        info = self.audio.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        
        input_devices = []
        for i in range(num_devices):
            device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
            if device_info.get('maxInputChannels') > 0:
                input_devices.append({
                    'index': i,
                    'name': device_info.get('name'),
                    'channels': device_info.get('maxInputChannels')
                })
                print(f"  [{i}] {device_info.get('name')}")
        
        if not input_devices:
            raise Exception("No input devices found!")
        
        # Use default device
        default_device = self.audio.get_default_input_device_info()
        default_index = default_device['index']
        print(f"\n[*] Using device [{default_index}]: {default_device['name']}")
        
        return default_index
    
    def _measure_ambient_noise(self, duration: float) -> float:
        """Measure ambient noise level."""
        energies = []
        num_chunks = int(duration * self.sample_rate / self.chunk_size)
        
        for _ in range(num_chunks):
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.float32)
                energy = np.sqrt(np.mean(audio_data ** 2))
                energies.append(energy)
            except Exception:
                continue
        
        if not energies:
            return 0.001
        
        # Use 80th percentile to ignore spikes
        energies.sort()
        percentile_80 = energies[int(len(energies) * 0.8)]
        return percentile_80
    
    def _measure_speaking_voice(self, duration: float) -> float:
        """Measure speaking voice level."""
        energies = []
        num_chunks = int(duration * self.sample_rate / self.chunk_size)
        
        for i in range(num_chunks):
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.float32)
                energy = np.sqrt(np.mean(audio_data ** 2))
                energies.append(energy)
                
                # Give feedback
                if i % 20 == 0:
                    bar_length = int(energy * 1000)
                    bar = "[*]" * min(bar_length, 50)
                    print(f"  Level: {bar}")
                    
            except Exception:
                continue
        
        if not energies:
            return 0.01
        
        # Use median of top 50% for speaking level
        energies.sort()
        top_50_percent = energies[len(energies)//2:]
        return np.median(top_50_percent) if top_50_percent else 0.01
    
    def _get_recommendations(self, ambient: float, speaking: float, snr: float) -> list:
        """Get recommendations based on calibration."""
        recommendations = []
        
        if ambient > 0.01:
            recommendations.append("High background noise detected - consider quieter environment")
        
        if speaking < 0.005:
            recommendations.append("Low microphone input - increase Windows microphone level")
        
        if snr < 3:
            recommendations.append("Poor signal quality - move closer to microphone")
        
        if not recommendations:
            recommendations.append("Good microphone setup detected")
        
        return recommendations
    
    def save_calibration(self, calibration: dict, config_path: Path):
        """Save calibration to config file."""
        try:
            # Load existing config
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update with calibration
            config['stt']['energy_threshold'] = calibration['energy_threshold']
            config['stt']['calibrated'] = True
            config['stt']['calibration_data'] = {
                'ambient_energy': calibration['ambient_energy'],
                'speaking_energy': calibration['speaking_energy'],
                'snr': calibration['signal_to_noise_ratio'],
                'time': calibration['calibration_time']
            }
            
            # Save back
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            print(f"[*] Calibration saved to {config_path}")
            
        except Exception as e:
            print(f"[ERROR] Failed to save calibration: {e}")

def run_calibration():
    """Run the calibration process."""
    calibrator = VoiceCalibrator()
    
    # Run calibration
    calibration = calibrator.calibrate_microphone()
    
    # Save to config
    config_path = Path(__file__).parent.parent.parent / "config.json"
    if config_path.exists():
        calibrator.save_calibration(calibration, config_path)
    
    return calibration

if __name__ == "__main__":
    run_calibration()
