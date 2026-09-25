@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Set_MEXC_Tier2_Secrets_V03.ps1"
pause
