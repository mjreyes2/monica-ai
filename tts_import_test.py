import time, traceback, os
os.environ['COQUI_TOS_AGREED'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
t0 = time.time()
f = open('C:/Monica/tts_import_result.txt', 'w')
f.write('START\n'); f.flush()

import librosa
f.write(f'librosa OK: {librosa.__version__} in {time.time()-t0:.1f}s\n'); f.flush()

try:
    from TTS.config.shared_configs import BaseDatasetConfig
    f.write(f'TTS BaseDatasetConfig OK in {time.time()-t0:.1f}s\n'); f.flush()
except Exception as e:
    f.write(f'TTS FAIL: {e}\n{traceback.format_exc()}\n'); f.flush()
    f.close()
    raise SystemExit(1)

try:
    from TTS.tts.configs.xtts_config import XttsConfig
    f.write(f'XttsConfig OK in {time.time()-t0:.1f}s\n'); f.flush()
except Exception as e:
    f.write(f'XttsConfig FAIL: {e}\n{traceback.format_exc()}\n'); f.flush()

f.write(f'ALL DONE in {time.time()-t0:.1f}s\n')
f.close()
