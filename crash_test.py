import sys
f = open('C:/Monica/crash_test.txt', 'w')
f.write('step1: starting\n'); f.flush()

try:
    import soxr
    f.write('soxr OK\n'); f.flush()
except Exception as e:
    f.write(f'soxr FAIL: {e}\n'); f.flush()

try:
    import librosa
    f.write(f'librosa OK: {librosa.__version__}\n'); f.flush()
except Exception as e:
    import traceback
    f.write(f'librosa FAIL: {e}\n{traceback.format_exc()}\n'); f.flush()

f.write('done\n'); f.close()
