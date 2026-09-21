@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0START_RADAR_RECOVERY_V0141.ps1"
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" (
  echo Radar recovery failed with exit code %RC%.
  echo Keep this window open and send the visible error or logs folder.
  pause
)
exit /b %RC%
