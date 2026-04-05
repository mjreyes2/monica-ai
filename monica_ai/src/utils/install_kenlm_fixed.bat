@echo off
echo Setting up Visual Studio environment...
call "C:\Program Files\Microsoft Visual Studio\18\Professional\VC\Auxiliary\Build\vcvars64.bat"

echo Setting CMake environment variables...
set CC=cl.exe
set CXX=cl.exe
set CMAKE_C_COMPILER=cl.exe
set CMAKE_CXX_COMPILER=cl.exe

echo Installing KenLM with explicit compiler settings...
python -m pip install --no-cache-dir https://github.com/kpu/kenlm/archive/master.zip

echo Done!
pause
