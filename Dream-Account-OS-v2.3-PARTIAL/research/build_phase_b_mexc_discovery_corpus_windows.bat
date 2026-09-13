@echo off
setlocal EnableExtensions

if "%~4"=="" (
  echo Usage:
  echo   %~nx0 RAW_DIR SYMBOL START_MONTH END_MONTH
  echo.
  echo Example:
  echo   %~nx0 ".\research\local_data\discovery_raw" BTCUSDT 2023-02 2024-12
  exit /b 2
)

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "RAW_DIR=%~f1"
set "SYMBOL=%~2"
set "START_MONTH=%~3"
set "END_MONTH=%~4"
set "OUTPUT_DIR=%SCRIPT_DIR%local_data\discovery_corpus\%SYMBOL%_%START_MONTH%_%END_MONTH%"
set "CORPUS_RECEIPT=%SCRIPT_DIR%local_data\intake\latest_discovery_corpus_receipt.json"
set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"

pushd "%PROJECT_ROOT%" >nul
python -m research.phase_b_mexc_discovery_corpus_v01 "%RAW_DIR%" --output-dir "%OUTPUT_DIR%" --symbol "%SYMBOL%" --start-month "%START_MONTH%" --end-month "%END_MONTH%" --receipt "%CORPUS_RECEIPT%"
set "RC=%ERRORLEVEL%"
popd >nul

if not "%RC%"=="0" (
  echo.
  echo Phase B Discovery corpus audit BLOCKED. No P00 evaluation was run.
  echo Sanitized corpus receipt, when available:
  echo   "%CORPUS_RECEIPT%"
  exit /b %RC%
)

echo.
echo Sanitized Discovery corpus receipt saved to:
echo   "%CORPUS_RECEIPT%"
echo.
echo Phase B Discovery corpus audit completed offline. No P00 evaluation was run.
exit /b 0
