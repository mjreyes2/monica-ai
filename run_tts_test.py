"""Launcher for TTS smoke test - sets env vars before any imports."""
import os
import sys

# Must be set BEFORE any imports that use numba/transformers
os.environ['NUMBA_DISABLE_JIT'] = '1'
os.environ['NUMBA_CACHE_DIR'] = r'C:\Users\Marvi\AppData\Local\Temp\numba_cache'
os.environ['COQUI_TOS_AGREED'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['TRANSFORMERS_OFFLINE'] = '0'
os.environ['HF_HUB_OFFLINE'] = '0'

print("Environment set. Running smoke test...", flush=True)
sys.stdout.flush()

# Now run the actual test
test_script = r'C:\Monica\data\training\monica_tts_training\test_coqui_trainer.py'
with open(test_script, 'r') as f:
    code = f.read()

exec(compile(code, test_script, 'exec'), {'__file__': test_script, '__name__': '__main__'})
