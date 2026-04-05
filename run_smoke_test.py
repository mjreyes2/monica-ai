import os, sys

# All env vars FIRST before any imports
os.environ['COQUI_TOS_AGREED'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['NUMBA_DISABLE_JIT'] = '1'

os.chdir(r'C:\Monica')
sys.path.insert(0, r'C:\Monica')

import runpy
runpy.run_path(
    r'C:\Monica\data\training\monica_tts_training\test_coqui_trainer.py',
    run_name='__main__'
)
