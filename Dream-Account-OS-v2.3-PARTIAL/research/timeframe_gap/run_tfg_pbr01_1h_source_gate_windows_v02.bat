@echo off
setlocal EnableExtensions

if "%~1"=="" (
  echo Usage: %~nx0 "PATH_TO_ORIGINAL_MEXC_RAW_DIR"
  exit /b 2
)

set "RAW_DIR=%~1"
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
set "FREEZE=%PROJECT_ROOT%\research\timeframe_gap\TFG_PBR01_1H_001_FREEZE.json"

if not exist "%FREEZE%" (
  echo BLOCKED_PRE_OUTCOME: frozen 1H authority file missing.
  exit /b 2
)

if not exist "%RAW_DIR%" (
  echo BLOCKED_PRE_OUTCOME: raw directory does not exist.
  exit /b 2
)

set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"
pushd "%PROJECT_ROOT%" >nul

echo ============================================================
echo TFG-PBR01-1H-001 SOURCE GATE V0.2
echo OUTCOME-BLIND / NO PNL / NO ORDERS / NO 2025 / NO 2026
echo ============================================================
echo.

echo [1/2] Frozen 2022-2024 local source inventory...
python -m research.timeframe_gap.tfg_pbr01_1h_source_inventory_gate_v02 --raw-dir "%RAW_DIR%" --freeze "%FREEZE%"
set "INVENTORY_RC=%ERRORLEVEL%"
echo.

echo [2/2] Public MEXC GET source-route probe at frozen boundaries...
python -m research.timeframe_gap.tfg_pbr01_1h_mexc_source_probe_v01
set "PROBE_RC=%ERRORLEVEL%"
echo.

popd >nul

echo ============================================================
echo SOURCE GATE SUMMARY
echo Inventory return code: %INVENTORY_RC%
echo Route probe return code: %PROBE_RC%
echo No trade outcome was evaluated by this launcher.
echo ============================================================

if not "%PROBE_RC%"=="0" exit /b 2
if "%INVENTORY_RC%"=="0" exit /b 0
exit /b 1
