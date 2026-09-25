@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0INSTALL_MEXC_OPTIONS_24X7_V03.ps1" -Live
set RC=%ERRORLEVEL%
echo.
if "%RC%"=="0" (echo OPTIONS V2.1 LIVE-GATED WATCHDOG ACTIVE) else (echo ACTIVATION FAILED - exit %RC%)
pause
exit /b %RC%
