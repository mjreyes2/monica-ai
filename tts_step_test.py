import time, traceback, os, sys
os.environ['COQUI_TOS_AGREED'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

f = open('C:/Monica/tts_step_log.txt', 'w')
def log(msg):
    f.write(f'{time.time():.1f} {msg}\n')
    f.flush()

log('START')

# Prevent TTS.__init__ from doing deep imports by mocking before import
log('Importing torch...')
import torch
log(f'torch OK: {torch.__version__}')

log('Importing TTS.config.shared_configs directly...')
# Import the submodule directly, bypassing TTS/__init__.py
import importlib
spec = importlib.util.find_spec('TTS.config.shared_configs')
log(f'found spec: {spec}')
module = importlib.util.module_from_spec(spec)
sys.modules['TTS.config.shared_configs'] = module
try:
    spec.loader.exec_module(module)
    log('TTS.config.shared_configs OK')
    BaseDatasetConfig = module.BaseDatasetConfig
    log(f'BaseDatasetConfig: {BaseDatasetConfig}')
except Exception as e:
    log(f'FAIL: {e}\n{traceback.format_exc()}')

f.close()
