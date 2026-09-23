@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo L2-RESILIENCY-001 - DRIVE RESTORE + SOURCE CLOCK V0.1A
echo Research-only: no sweeps, no returns, no PnL, no 2026.
echo ============================================================
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_L2R_2025_DRIVE_RESTORE_AND_SOURCE_CLOCK_V01A.ps1" %*
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" (
  echo FAIL-CLOSED - exit code %RC%
) else (
  echo COMPLETE - check Desktop\L2R_2025_BTC_VALIDATION_LOCAL
)
echo.
pause
exit /b %RC%
