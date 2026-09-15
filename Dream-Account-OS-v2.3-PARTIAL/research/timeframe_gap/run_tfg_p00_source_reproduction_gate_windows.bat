@echo off
setlocal EnableExtensions

if "%~1"=="" (
  echo Usage:
  echo   %~nx0 RAW_DIR
  echo.
  echo Example:
  echo   %~nx0 "%USERPROFILE%\Downloads\MEXC_P00_CANONICAL"
  exit /b 2
)

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."
set "RAW_DIR=%~f1"
set "WORK_DIR=%SCRIPT_DIR%receipts\p00_source_reproduction_work"
set "RECEIPT=%SCRIPT_DIR%receipts\TFG_P00_SOURCE_REPRODUCTION_RECEIPT_V0.1.json"
set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"

pushd "%PROJECT_ROOT%" >nul
python -m research.timeframe_gap.tfg_p00_source_reproduction_gate_v01 "%RAW_DIR%" --work-dir "%WORK_DIR%" --receipt "%RECEIPT%"
set "RC=%ERRORLEVEL%"
popd >nul

if not "%RC%"=="0" (
  echo.
  echo TFG P00 exact source reproduction gate BLOCKED.
  echo No P00 outcome evaluation was run.
  echo Receipt:
  echo   "%RECEIPT%"
  exit /b %RC%
)

echo.
echo TFG P00 exact source reproduction gate PASSED 6/6.
echo No P00 outcome evaluation was run.
echo Receipt:
echo   "%RECEIPT%"
exit /b 0
