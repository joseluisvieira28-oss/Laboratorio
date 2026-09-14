@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0show_gate_k_phase_a_scheduler_status.ps1"
exit /b %ERRORLEVEL%
