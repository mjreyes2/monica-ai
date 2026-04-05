import sounddevice as sd

print("NVIDIA Broadcast Devices:")
for i, device in enumerate(sd.query_devices()):
    if 'nvidia' in device['name'].lower() or 'broadcast' in device['name'].lower():
        print(f"Index {i}: {device['name']} (Inputs: {device['max_input_channels']}, Outputs: {device['max_output_channels']})")
