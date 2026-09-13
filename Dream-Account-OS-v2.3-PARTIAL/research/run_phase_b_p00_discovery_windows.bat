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
set "RECEIPT=%OUTPUT_DIR%\latest_p00_discovery_receipt.json"

if not exist "%RAW_DIR%" (
  echo Phase B P00 Discovery BLOCKED: raw directory not found.
  exit /b 2
)

set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"

pushd "%PROJECT_ROOT%" >nul
python -m research.phase_b_p00_discovery_runner_v01 "%RAW_DIR%" --output-dir "%OUTPUT_DIR%" --receipt "%RECEIPT%"
set "RC=%ERRORLEVEL%"
popd >nul

if not "%RC%"=="0" (
  echo.
  echo Phase B P00 Discovery BLOCKED. No 2025/2026 access or exchange mutation was performed.
  echo Sanitized receipt, when available:
  echo   "%RECEIPT%"
  exit /b %RC%
)

echo.
echo Phase B P00 Discovery completed OFFLINE under the frozen prospective authority.
echo No 2025/2026 data was read. No exchange mutation or live trade was performed.
echo Receipt:
echo   "%RECEIPT%"
exit /b 0
