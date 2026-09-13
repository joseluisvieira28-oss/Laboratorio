@echo off
setlocal

if "%~1"=="" (
  echo Usage: %~nx0 RAW_DIR
  exit /b 64
)

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "RAW_DIR=%~f1"
set "OUTPUT_DIR=%PROJECT_ROOT%\research\local_data\intake"
set "RECEIPT=%OUTPUT_DIR%\latest_p00_discovery_postmortem.json"
set "LEDGER=%OUTPUT_DIR%\latest_p00_discovery_postmortem_trades.csv"

if not exist "%RAW_DIR%" (
  echo Phase B P00 post-mortem BLOCKED: raw directory not found.
  exit /b 2
)

set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"

pushd "%PROJECT_ROOT%" >nul
python -m research.phase_b_p00_discovery_postmortem_v01 "%RAW_DIR%" --output-dir "%OUTPUT_DIR%" --receipt "%RECEIPT%" --ledger "%LEDGER%"
set "RC=%ERRORLEVEL%"
popd >nul

if not "%RC%"=="0" (
  echo.
  echo Phase B P00 post-mortem BLOCKED. P00 remains CLOSED NO_EDGE.
  echo No 2025/2026 access or exchange mutation was performed.
  exit /b %RC%
)

echo.
echo Phase B P00 Discovery post-mortem completed OFFLINE and DIAGNOSTIC-ONLY.
echo P00 remains CLOSED NO_EDGE. No subgroup may rescue or retune P00.
echo No 2025/2026 data was read. No exchange mutation or live trade was performed.
echo Receipt:
echo   "%RECEIPT%"
echo Trade ledger:
echo   "%LEDGER%"
exit /b 0
