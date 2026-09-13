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
set "RECEIPT=%OUTPUT_DIR%\latest_p00_sensitivity_matrix.json"

if not exist "%RAW_DIR%" (
  echo Phase B P00 sensitivity matrix BLOCKED: raw directory not found.
  exit /b 2
)

set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"

pushd "%PROJECT_ROOT%" >nul
python -m research.phase_b_p00_sensitivity_matrix_v01 "%RAW_DIR%" --output-dir "%OUTPUT_DIR%" --receipt "%RECEIPT%"
set "RC=%ERRORLEVEL%"
popd >nul

if not "%RC%"=="0" (
  echo.
  echo Phase B P00 sensitivity matrix BLOCKED. P00 remains CLOSED NO_EDGE.
  echo No profile is promoted. No 2025/2026 access or exchange mutation was performed.
  exit /b %RC%
)

echo.
echo Phase B P00 pre-registered P01-P12 sensitivity matrix completed OFFLINE and DIAGNOSTIC-ONLY.
echo P00 remains CLOSED NO_EDGE. No sensitivity profile may rescue, replace or retune P00.
echo No winner is selected. No 2025/2026 data was read. No exchange mutation or live trade was performed.
echo Receipt:
echo   "%RECEIPT%"
exit /b 0
