@echo off
title MONICA AI - Service Architecture
color 0A

REM Change to project directory
cd /d "C:\Monica"

echo ============================================================
echo         MONICA AI - Multi-Process Service Architecture
echo ============================================================
echo.
echo Starting Monica with fault-tolerant architecture...
echo.


REM Use venv Python with multiprocessing support if available, else fallback to system python
IF EXIST .venv\Scripts\python.exe (
	.venv\Scripts\python.exe monica_services_launcher.py
) ELSE (
	python monica_services_launcher.py
)

echo.
pause
