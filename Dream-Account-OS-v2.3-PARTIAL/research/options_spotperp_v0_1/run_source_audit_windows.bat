@echo off
setlocal
cd /d "%~dp0"

echo OPTIONS-SPOTPERP-001 - SOURCE AUDIT V0.1
echo =========================================
echo Research-only. No outcomes. No PnL. No 2025/2026.
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
echo Running full frozen source audit...
%PY% source_audit.py --output ".\source_audit_data"
set "RC=%errorlevel%"

echo.
if "%RC%"=="0" (
  echo SOURCE_AUDIT_PASS
  echo See source_audit_data\source_audit_report.json
) else if "%RC%"=="4" (
  echo PROBE_ONLY_NO_DECISION
) else (
  echo SOURCE_AUDIT_BLOCKED
  echo See source_audit_data\source_audit_report.json if present.
)

exit /b %RC%
