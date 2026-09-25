@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0STOP_MEXC_OPTIONS_24X7_V03.ps1"
pause
