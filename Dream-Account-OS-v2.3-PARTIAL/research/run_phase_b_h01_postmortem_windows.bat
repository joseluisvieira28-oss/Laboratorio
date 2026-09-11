@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem H01 CLOSED_NO_EDGE descriptive post-mortem. OFFLINE ONLY.
rem Reproduces the exact already-open Discovery run before diagnostics.
rem Does not unlock 2025-09..12 or 2026, does not simulate H02, and never trades.

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "RAW_DIR=%PROJECT_ROOT%\research\local_data\h01_discovery_raw"
set "OUTPUT_DIR=%PROJECT_ROOT%\research\local_data\h01_discovery_output"

pushd "%PROJECT_ROOT%" >nul 2>&1
if errorlevel 1 (
  echo BLOCKED: unable to enter project root.
  exit /b 2
)

set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"

echo.
echo ============================================================
echo H01 Discovery Post-Mortem - DESCRIPTIVE ONLY
echo H01 status: CLOSED_NO_EDGE
echo Reproduction corpus: already-open 2025-01 through 2025-08 ONLY
echo Validation 2025-09..12: LOCKED
echo Holdout 2026: LOCKED
echo H01 retuning / rescue: FORBIDDEN
echo H02 simulation / candidate selection: NOT PERFORMED
echo Network / exchange mutation / live trading: DISABLED
echo ============================================================
echo.

python -m research.phase_b_h01_discovery_postmortem_v01 "%RAW_DIR%" "%OUTPUT_DIR%"
set "RC=!ERRORLEVEL!"

if not "!RC!"=="0" (
  echo.
  echo H01 post-mortem BLOCKED. No governance lock was weakened.
  popd
  exit /b !RC!
)

echo.
echo H01 post-mortem completed. Review:
echo   research\local_data\h01_discovery_output\h01_postmortem\latest_h01_postmortem_receipt.json
echo   research\local_data\h01_discovery_output\h01_postmortem\latest_h01_trade_ledger.csv

popd
exit /b 0
