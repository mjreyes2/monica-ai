import sounddevice as sd

def list_audio_devices():
    print("\nAvailable audio devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        input_channels = device.get('max_input_channels', 0)
        output_channels = device.get('max_output_channels', 0)
        sample_rate = device.get('default_samplerate', 'N/A')
        
        device_type = []
        if input_channels > 0:
            device_type.append(f"Inputs: {input_channels}")
        if output_channels > 0:
            device_type.append(f"Outputs: {output_channels}")
            
        print(f"{i}: {device['name']} ({', '.join(device_type)}) | Sample Rate: {sample_rate} Hz")

if __name__ == "__main__":
    list_audio_devices()
