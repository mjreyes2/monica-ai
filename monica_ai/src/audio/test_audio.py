import sounddevice as sd
import numpy as np
import time

def list_audio_devices():
    print("\nAvailable audio devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']} (Inputs: {device['max_input_channels']}, Outputs: {device['max_output_channels']})")
    return devices

def test_recording(duration=3, fs=44100):
    print("\nTesting audio recording...")
    print(f"Recording for {duration} seconds... (speak into your microphone)")
    
    try:
        # Record audio
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
        sd.wait()  # Wait until recording is finished
        
        # Calculate some basic stats
        rms = np.sqrt(np.mean(recording**2))
        max_amp = np.max(np.abs(recording))
        
        print(f"\nRecording complete!")
        print(f"- Duration: {len(recording)/fs:.2f} seconds")
        print(f"- RMS level: {rms:.6f}")
        print(f"- Maximum amplitude: {max_amp:.6f}")
        
        if rms < 0.01:  # Arbitrary threshold for detecting silence
            print("\nWARNING: The recording seems very quiet. Check your microphone connection and volume.")
        else:
            print("\nSuccess! Audio input appears to be working.")
            
        return True
        
    except Exception as e:
        print(f"\nError during recording: {e}")
        return False

if __name__ == "__main__":
    print("Audio Recorder Test")
    print("==================")
    
    # List available audio devices
    devices = list_audio_devices()
    
    # Try to use the default input device
    default_input = sd.default.device[0]
    print(f"\nUsing default input device: {devices[default_input]['name']}")
    
    # Test recording
    if test_recording():
        print("\nAudio recording test completed successfully!")
    else:
        print("\nAudio recording test failed. Please check your audio settings.")
