@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo ONCHAIN-CAPFLOW-001 V0.1A - DATA SOURCE + DATA AUDIT GATE
echo ============================================================
echo Research-only. No live trading. 2025 and 2026 must remain unopened.
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo BLOCKED: Python was not found in PATH.
  echo Install Python 3 and re-run this file. No data was acquired.
  exit /b 10
)

python --version
if errorlevel 1 (
  echo BLOCKED: Python could not start.
  exit /b 11
)

echo.
echo [GATE A+B] Data source gate, frozen acquisition and SHA256 manifest...
python acquire_data.py --output .\data
set ACQ=%ERRORLEVEL%
if "%ACQ%"=="12" (
  echo.
  echo STOP: EXECUTION_ENVIRONMENT_BLOCKED.
  echo This is a DNS/network/transport problem, NOT a scientific DATA_BLOCKED verdict.
  echo Review .\data\data_gate_status.json if present, fix connectivity, then re-run unchanged.
  exit /b 12
)
if not "%ACQ%"=="0" (
  echo.
  echo STOP: acquisition/data-source gate did not PASS. Exit code %ACQ%.
  echo Do NOT substitute another provider or edit the frozen protocol.
  echo Review .\data\data_gate_status.json if present.
  exit /b %ACQ%
)

echo.
echo [GATE C] Data audit only - no outcome metrics...
python audit_data.py --data .\data
set AUD=%ERRORLEVEL%
if not "%AUD%"=="0" (
  echo.
  echo STOP: DATA AUDIT did not PASS. Exit code %AUD%.
  echo Do NOT create or run Discovery.
  echo Review .\data\data_audit_report.json.
  exit /b %AUD%
)

echo.
echo ============================================================
echo DATA_AUDIT_PASS
echo ============================================================
echo Expected artifacts:
echo   .\data\data_gate_status.json
echo   .\data\raw_manifest.json
echo   .\data\data_audit_report.json
echo.
echo Discovery is NOT executed by this file.
echo Record the PASS in Drive before authorizing Discovery.
exit /b 0
