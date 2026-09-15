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
set "OUTPUT_DIR=%SCRIPT_DIR%receipts\pbr01_1d_preflight"
set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"

pushd "%PROJECT_ROOT%" >nul
python -m research.timeframe_gap.tfg_pbr01_1d_preflight_runner_v01 --raw-dir "%RAW_DIR%" --output-dir "%OUTPUT_DIR%"
set "RC=%ERRORLEVEL%"
popd >nul

if not "%RC%"=="0" (
  echo.
  echo TFG-PBR01-1D-001 preflight BLOCKED.
  echo No signal geometry or outcome evaluation was run.
  echo Receipt:
  echo   "%OUTPUT_DIR%\TFG_PBR01_1D_PREOUTCOME_PREFLIGHT_V0.1.json"
  exit /b %RC%
)

echo.
echo TFG-PBR01-1D-001 preflight PASSED source/aggregation audit only.
echo Lab remains NOT ACTIVATED and queue-locked.
echo No signal geometry or outcome evaluation was run.
echo Receipt:
  echo   "%OUTPUT_DIR%\TFG_PBR01_1D_PREOUTCOME_PREFLIGHT_V0.1.json"
exit /b 0
