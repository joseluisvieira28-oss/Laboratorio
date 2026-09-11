@echo off
setlocal EnableExtensions

if "%~6"=="" (
  echo Usage:
  echo   %~nx0 RAW_CSV CANONICAL_CSV ADAPTER_RECEIPT SYMBOL DECLARED_START_UTC DECLARED_END_UTC
  echo.
  echo Example:
  echo   %~nx0 ".\research\local_data\intake\BTC_USDT-Min15-2023-02-01.csv" ".\research\local_data\intake\canonical\BTC_USDT-Min15-2023-02-01.canonical.csv" ".\research\local_data\intake\latest_adapter_receipt.json" BTCUSDT 2023-02-01T00:00:00Z 2023-02-28T23:59:59.999Z
  exit /b 2
)

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "RAW_SOURCE=%~f1"
set "CANONICAL_SOURCE=%~f2"
set "ADAPTER_RECEIPT=%~f3"
set "SYMBOL=%~4"
set "DECLARED_START=%~5"
set "DECLARED_END=%~6"
set "EVIDENCE_DIR=%SCRIPT_DIR%local_data\intake"
set "AUDIT_RECEIPT=%EVIDENCE_DIR%\latest_adapter_bound_audit.json"
set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"

if not exist "%EVIDENCE_DIR%" mkdir "%EVIDENCE_DIR%"

pushd "%PROJECT_ROOT%" >nul
python -m research.phase_b_mexc_adapter_audit_binding_v01 "%RAW_SOURCE%" "%CANONICAL_SOURCE%" "%ADAPTER_RECEIPT%" --symbol "%SYMBOL%" --declared-start "%DECLARED_START%" --declared-end "%DECLARED_END%" --receipt-out "%AUDIT_RECEIPT%"
set "RC=%ERRORLEVEL%"
popd >nul

if not "%RC%"=="0" (
  echo.
  echo Phase B adapter-bound audit BLOCKED. No P00 evaluation was run.
  echo Sanitized audit receipt, when available:
  echo   "%AUDIT_RECEIPT%"
  exit /b %RC%
)

echo.
echo Sanitized adapter-bound audit receipt saved to:
echo   "%AUDIT_RECEIPT%"
echo.
echo Phase B adapter-bound audit completed offline. No P00 evaluation was run.
exit /b 0
