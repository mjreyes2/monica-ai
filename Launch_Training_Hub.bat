@echo off
setlocal
cd /d C:\Monica

set "VENV=C:\Monica\new"
if exist "%VENV%\Scripts\python.exe" (
  "%VENV%\Scripts\python.exe" scripts\training_hub_gui.py
) else (
  py scripts\training_hub_gui.py
)

endlocal
