@echo off
setlocal
cd /d "%~dp0"
echo ============================================================
echo L2-RESILIENCY-001 - FROZEN 2025 VALIDATION V0.1B
echo 2025 ONLY - NO PNL - NO COSTS - NO SHARPE - NO 2026 - NO ORDERS
echo ============================================================
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0RUN_L2R_2025_DRIVE_RESTORE_AND_VALIDATION_V01B.ps1" %*
set RC=%ERRORLEVEL%
echo.
if not "%RC%"=="0" (
  echo FAIL-CLOSED - exit code %RC%
) else (
  echo COMPLETE - evidence is under Desktop\L2R_2025_BTC_VALIDATION_LOCAL
)
echo.
pause
exit /b %RC%
