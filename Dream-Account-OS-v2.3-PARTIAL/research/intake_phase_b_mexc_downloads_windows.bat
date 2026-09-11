@echo off
setlocal EnableExtensions

if "%~4"=="" (
  echo Usage:
  echo   %~nx0 SOURCE_DOWNLOAD_DIR SYMBOL START_MONTH END_MONTH
  echo.
  echo Example:
  echo   %~nx0 "%USERPROFILE%\Downloads" BTCUSDT 2023-02 2024-12
  exit /b 2
)

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "SOURCE_DIR=%~f1"
set "SYMBOL=%~2"
set "START_MONTH=%~3"
set "END_MONTH=%~4"
set "DEST_DIR=%SCRIPT_DIR%local_data\discovery_raw"
set "RECEIPT=%SCRIPT_DIR%local_data\intake\latest_download_intake_receipt.json"
set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"

pushd "%PROJECT_ROOT%" >nul
python -m research.phase_b_mexc_download_intake_v01 "%SOURCE_DIR%" --destination-dir "%DEST_DIR%" --symbol "%SYMBOL%" --start-month "%START_MONTH%" --end-month "%END_MONTH%" --receipt "%RECEIPT%"
set "RC=%ERRORLEVEL%"
popd >nul

if not "%RC%"=="0" (
  echo.
  echo Phase B MEXC download intake BLOCKED. No P00 evaluation was run.
  echo Sanitized intake receipt, when available:
  echo   "%RECEIPT%"
  exit /b %RC%
)

echo.
echo Sanitized download-intake receipt saved to:
echo   "%RECEIPT%"
echo.
echo Phase B MEXC download intake completed offline. Missing months may remain. No P00 evaluation was run.
exit /b 0
