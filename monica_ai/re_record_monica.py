import sounddevice as sd
import soundfile as sf
import numpy as np
from pathlib import Path

output_dir = Path('voice_recordings')
output_dir.mkdir(exist_ok=True)

for i in range(3):
    phrase = 'Monica initialize'
    filename = f'phrase_{i:02d}_Monica_initialize.wav'
    filepath = output_dir / filename
    
    print(f'\nRecording #{i+1}: "{phrase}"')
    print('Press ENTER to start, speak clearly, then ENTER to stop...')
    input()
    
    print('Recording... (speak now)')
    recording = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype=np.float32)
    input()
    
    sd.stop()
    
    sf.write(filepath, recording, 16000)
    print(f'Saved: {filepath}')

print('\nRe-recorded Monica initialize phrases!')
