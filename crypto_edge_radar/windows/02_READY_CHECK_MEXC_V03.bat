@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run_MEXC_Tier2_Ready_Check_V03.ps1"
set RC=%ERRORLEVEL%
echo.
if "%RC%"=="0" (echo READY CHECK PASS) else (echo READY CHECK BLOCKED - exit %RC%)
pause
exit /b %RC%
