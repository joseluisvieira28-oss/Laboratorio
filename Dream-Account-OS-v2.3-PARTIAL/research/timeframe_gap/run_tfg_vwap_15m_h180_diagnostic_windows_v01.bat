@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
set "OUTPUT_DIR=%PROJECT_ROOT%\research\local_data\tfg_vwap_15m_source_gate"
set "RECEIPT=%OUTPUT_DIR%\TFG_VWAP_15M_H180_LOCAL_ARTIFACT_DIAGNOSTIC_V0.1.json"

echo ============================================================
echo TFG-VWAP-15M-001 H180 LOCAL ARTIFACT DIAGNOSTIC V0.1
echo FILENAME-ONLY / NO ZIP OPEN / NO MARKET ROWS / NO OUTCOMES
echo ============================================================

set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"
pushd "%PROJECT_ROOT%" >nul
python -m research.timeframe_gap.diagnose_h180_local_artifacts_v01 --project-root "%PROJECT_ROOT%" --receipt "%RECEIPT%"
set "RC=%ERRORLEVEL%"
popd >nul

echo.
echo Diagnostic receipt:
echo   "%RECEIPT%"
echo No ZIP was opened. No market row, return, PnL, 2024, 2025, or 2026 outcome data was inspected.
exit /b %RC%
