# Audio configuration for voice training application

# Device indices
INPUT_DEVICE_INDEX = 2  # Microphone (NVIDIA Broadcast)
OUTPUT_DEVICE_INDEX = 4  # Speakers (NVIDIA Broadcast)

# Audio settings
SAMPLE_RATE = 48000  # Using 48kHz for better quality
CHANNELS = 1  # Mono audio
CHUNK_SIZE = 1024  # Number of frames per buffer
