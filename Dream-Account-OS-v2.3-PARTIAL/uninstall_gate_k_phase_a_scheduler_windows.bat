@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall_gate_k_phase_a_scheduler.ps1" %*
set "EXITCODE=%ERRORLEVEL%"
if not "%EXITCODE%"=="0" (
  echo Gate K Phase A scheduler removal failed. Exit code: %EXITCODE%
  exit /b %EXITCODE%
)
exit /b 0
