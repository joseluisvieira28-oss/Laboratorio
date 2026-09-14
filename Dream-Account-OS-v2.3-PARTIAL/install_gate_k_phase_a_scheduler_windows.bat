@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_gate_k_phase_a_scheduler.ps1" %*
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo.
  echo Gate K Phase A scheduler installation BLOCKED or failed closed. Exit code: %EXITCODE%
  exit /b %EXITCODE%
)
echo.
echo Gate K Phase A scheduler installation completed.
exit /b 0
