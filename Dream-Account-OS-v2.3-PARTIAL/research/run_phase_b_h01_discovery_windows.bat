@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem Authorized H01 Discovery launcher. OFFLINE ONLY.
rem Reads only exact 2025-01..2025-08 official MEXC Spot 15m CSV filenames.
rem Does not download data, does not access 2025-09..12 or 2026, and never trades.

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "SOURCE_DIR=%~1"

if "%SOURCE_DIR%"=="" set "SOURCE_DIR=%USERPROFILE%\Downloads"

pushd "%PROJECT_ROOT%" >nul 2>&1
if errorlevel 1 (
  echo BLOCKED: unable to enter project root.
  exit /b 2
)

set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"

echo.
echo ============================================================
echo H01 Discovery - AUTHORIZED OFFLINE RUN
echo Source directory: "%SOURCE_DIR%"
echo Authorized months: 2025-01 through 2025-08 ONLY
echo Validation 2025-09..12: LOCKED
echo Holdout 2026: LOCKED
echo Network download: DISABLED
echo Exchange mutation / live trading: DISABLED
echo ============================================================
echo.

python -m research.phase_b_h01_local_discovery_orchestrator_v01 "%SOURCE_DIR%"
set "RC=!ERRORLEVEL!"

if not "!RC!"=="0" (
  echo.
  echo H01 Discovery did not complete. Review:
  echo   research\local_data\h01_discovery_output\latest_h01_local_orchestrator_summary.json
  popd
  exit /b !RC!
)

echo.
echo H01 Discovery completed. Review:
echo   research\local_data\h01_discovery_output\latest_h01_discovery_receipt.json

popd
exit /b 0
