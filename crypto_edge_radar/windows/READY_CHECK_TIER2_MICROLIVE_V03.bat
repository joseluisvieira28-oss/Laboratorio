@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Run_Tier2_MicroLive_Ready_Check_V03.ps1" %*
set EC=%ERRORLEVEL%
echo.
if not "%EC%"=="0" (
  echo LIVE-GO READY CHECK BLOCKED. No order was created.
) else (
  echo LIVE-GO INFRA ARMED. Waiting for a canonical eligible signal.
)
pause
exit /b %EC%
