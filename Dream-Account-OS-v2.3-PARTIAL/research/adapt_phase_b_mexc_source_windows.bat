@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "PYTHONPATH=%PROJECT_ROOT%;%PROJECT_ROOT%\src;%PYTHONPATH%"
set "EVIDENCE_DIR=%SCRIPT_DIR%local_data\intake"
set "CANONICAL_DIR=%EVIDENCE_DIR%\canonical"
set "RECEIPT_FILE=%EVIDENCE_DIR%\latest_adapter_receipt.json"

if "%~1"=="" (
  echo Usage:
  echo   adapt_phase_b_mexc_source_windows.bat "C:\path\to\official_mexc_15m_csv"
  echo.
  echo This runs only the frozen offline adapter. It does NOT run P00.
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
if not exist "%CANONICAL_DIR%" mkdir "%CANONICAL_DIR%" >nul 2>&1
if not exist "%CANONICAL_DIR%" (
  echo BLOCKED: could not create canonical output directory.
  exit /b 2
)

for %%F in ("%SOURCE_FILE%") do set "SOURCE_STEM=%%~nF"
set "CANONICAL_FILE=%CANONICAL_DIR%\%SOURCE_STEM%.canonical.csv"

pushd "%PROJECT_ROOT%" >nul
python -m research.phase_b_mexc_bulk_csv_adapter_v01 "%SOURCE_FILE%" --canonical "%CANONICAL_FILE%" --receipt "%RECEIPT_FILE%" > "%EVIDENCE_DIR%\latest_adapter_console.json"
set "RC=%ERRORLEVEL%"
popd >nul

if exist "%RECEIPT_FILE%" (
  type "%RECEIPT_FILE%"
  echo.
  echo Sanitized adapter receipt saved to:
  echo   "%RECEIPT_FILE%"
)

if not "%RC%"=="0" (
  echo.
  echo Phase B MEXC adapter ended BLOCKED. No P00 evaluation was run.
  exit /b %RC%
)

echo.
echo Canonical output written to:
  echo   "%CANONICAL_FILE%"
echo.
echo Phase B MEXC adapter completed in offline adapter-only mode. No P00 evaluation was run.
exit /b 0
