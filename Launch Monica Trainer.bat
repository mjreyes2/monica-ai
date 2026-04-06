@echo off
title Monica Trainer
cd /d "%~dp0"
python scripts\monica_trainer.py
if errorlevel 1 (
    echo.
    echo ERROR: Monica Trainer failed to start. See message above.
    pause
)
