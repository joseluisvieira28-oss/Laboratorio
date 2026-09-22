@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0UPGRADE_RADAR_V0144.ps1"
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" (
  echo Radar V0.14.4 upgrade failed or rolled back with exit code %RC%.
  echo Keep this window open and send the visible error or logs folder.
  pause
) else (
  echo Radar V0.14.4 upgrade completed successfully.
  pause
)
exit /b %RC%
