@echo off
cd /d "%~dp0"
set "KS=%~dp0..\KILL_SWITCH"
if exist "%KS%" (
  del /f /q "%KS%"
  echo KILL_SWITCH removed. Live watchdog is NOT restarted automatically.
) else (
  echo KILL_SWITCH was not present.
)
echo Run 02_READY_CHECK first, then 03_ACTIVATE only when you intentionally want live mode armed.
pause
