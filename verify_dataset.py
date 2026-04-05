import json, os
from pathlib import Path

os.environ['COQUI_TOS_AGREED'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

meta = r'C:\Monica\data\training\monica_tts_training\datasets\monica_combined\combined_metadata.json'
with open(meta, encoding='utf-8-sig') as f:
    data = json.load(f)

print(f'Total samples: {len(data)}')
print(f'First path: {data[0]["audio_file"]}')
exists = sum(1 for d in data[:50] if Path(d['audio_file']).exists())
print(f'First 50 audio files exist: {exists}/50')
