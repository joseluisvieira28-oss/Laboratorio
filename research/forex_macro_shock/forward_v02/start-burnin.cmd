@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if not exist ".venv\Scripts\python.exe" exit /b 1
".venv\Scripts\python.exe" -m pip install -r requirements-runtime.txt
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" supervisor.py
