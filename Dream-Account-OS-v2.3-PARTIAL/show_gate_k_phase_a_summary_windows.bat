@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Gate K Phase A — compact operational summary
REM READ-ONLY. This launcher does not contact the exchange and does not mutate campaign evidence.

cd /d "%~dp0"

if defined PYTHONPATH (
  set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
) else (
  set "PYTHONPATH=%CD%\src"
)

set "JOURNAL=%CD%\gate_k_phase_a_evidence\phase_a_campaign.sqlite3"

if not exist "%JOURNAL%" (
  echo BLOCKED: Phase A campaign journal not found.
  echo Expected: %JOURNAL%
  exit /b 2
)

where py >nul 2>nul
if !ERRORLEVEL!==0 (
  py -3 -m dream_account.execution_phase_a_campaign_summary --journal "%JOURNAL%"
  set "RC=!ERRORLEVEL!"
  exit /b !RC!
)

where python >nul 2>nul
if !ERRORLEVEL!==0 (
  python -m dream_account.execution_phase_a_campaign_summary --journal "%JOURNAL%"
  set "RC=!ERRORLEVEL!"
  exit /b !RC!
)

echo BLOCKED: Python 3 was not found in PATH.
exit /b 2
