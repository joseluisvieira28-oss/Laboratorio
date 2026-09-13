@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "PYTHONPATH=%PROJECT_ROOT%;%PROJECT_ROOT%\src;%PYTHONPATH%"
set "EVIDENCE_DIR=%SCRIPT_DIR%local_data\intake"
set "RECEIPT_FILE=%EVIDENCE_DIR%\latest_schema_probe.json"

if "%~1"=="" (
  echo Usage:
  echo   probe_phase_b_mexc_source_windows.bat "C:\path\to\official_mexc_file.csv_or_zip_or_json"
  echo.
  echo You may also drag and drop the source file onto this BAT file.
  exit /b 2
)

set "SOURCE_FILE=%~f1"
if not exist "%SOURCE_FILE%" (
  echo BLOCKED: source file not found.
  exit /b 2
)

where python >nul 2>&1
if errorlevel 1 (
  echo BLOCKED: Python was not found on PATH.
  exit /b 2
)

if not exist "%EVIDENCE_DIR%" mkdir "%EVIDENCE_DIR%" >nul 2>&1
if not exist "%EVIDENCE_DIR%" (
  echo BLOCKED: could not create local intake evidence directory.
  exit /b 2
)

pushd "%PROJECT_ROOT%" >nul
python -m research.phase_b_mexc_schema_probe_v01 "%SOURCE_FILE%" > "%RECEIPT_FILE%"
set "RC=%ERRORLEVEL%"
popd >nul

if exist "%RECEIPT_FILE%" (
  type "%RECEIPT_FILE%"
  echo.
  echo Sanitized schema-probe receipt saved to:
  echo   "%RECEIPT_FILE%"
)

if not "%RC%"=="0" (
  echo.
  echo Phase B schema probe ended BLOCKED. No P00 evaluation was run.
  exit /b %RC%
)

echo.
echo Phase B schema probe completed in structure-only mode. No market values or P00 outcome metrics were returned.
exit /b 0
