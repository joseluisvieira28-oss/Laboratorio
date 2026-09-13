@echo off
setlocal
cd /d "%~dp0"

echo OPTIONS-SPOTPERP-001 - FINAL SOURCE/DATA GATE V0.1
echo ===================================================
echo Research-only. No skew. No signals. No returns. No PnL. No 2025/2026.
echo.

where py >nul 2>&1
if %errorlevel%==0 (
  set "PY=py"
  goto :run
)

where python >nul 2>&1
if %errorlevel%==0 (
  set "PY=python"
  goto :run
)

echo BLOCKED: Python 3 was not found in PATH.
echo Install Python 3 and retry. Nothing was downloaded.
exit /b 2

:run
%PY% --version
if errorlevel 1 (
  echo BLOCKED: Python could not start.
  exit /b 2
)

echo.
echo Running final frozen source/data gate...
%PY% source_audit_gate.py --output ".\source_audit_data"
set "RC=%errorlevel%"

echo.
if "%RC%"=="0" (
  echo SOURCE_AUDIT_PASS
  echo Final receipt: source_audit_data\source_gate_receipt.json
) else if "%RC%"=="4" (
  echo PROBE_ONLY_NO_DECISION
  echo Final receipt: source_audit_data\source_gate_receipt.json
) else if "%RC%"=="12" (
  echo EXECUTION_ENVIRONMENT_BLOCKED
  echo DNS/network/transport problem only - NOT a scientific source verdict.
  echo Final receipt: source_audit_data\source_gate_receipt.json if present.
) else (
  echo SOURCE_AUDIT_BLOCKED
  echo Final receipt: source_audit_data\source_gate_receipt.json if present.
)

exit /b %RC%
