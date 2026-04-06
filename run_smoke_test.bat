@echo off
set NUMBA_DISABLE_JIT=1
set NUMBA_CACHE_DIR=C:\Monica\numba_cache
set COQUI_TOS_AGREED=1
set TOKENIZERS_PARALLELISM=false
set TRANSFORMERS_OFFLINE=0
set HF_HUB_OFFLINE=0
set PYTHONIOENCODING=utf-8

cd /d C:\Monica
C:\Monica\new\Scripts\python.exe data\training\scripts\tts\test_coqui_trainer.py > C:\Monica\smoke_test_out.txt 2> C:\Monica\smoke_test_err.txt
echo Exit code: %ERRORLEVEL%
