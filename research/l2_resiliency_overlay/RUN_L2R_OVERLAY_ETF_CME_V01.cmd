@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_L2R_OVERLAY_ETF_CME_V01.ps1"
set RC=%ERRORLEVEL%
if not "%RC%"=="0" (
  echo.
  echo FAIL-CLOSED - exit code %RC%
  pause
  exit /b %RC%
)
echo.
echo COMPLETE
pause
