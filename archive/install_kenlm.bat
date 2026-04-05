@echo off
echo Setting up Visual Studio environment...
call "C:\Program Files\Microsoft Visual Studio\18\Professional\VC\Auxiliary\Build\vcvars64.bat"

echo Installing KenLM...
python -m pip install https://github.com/kpu/kenlm/archive/master.zip

echo Done!
pause
