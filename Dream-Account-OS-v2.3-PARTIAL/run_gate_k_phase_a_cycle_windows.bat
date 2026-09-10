@echo off
setlocal EnableExtensions

REM Gate K Phase A — local one-shot launcher
REM SHADOW / READ-ONLY only. This file never contains credentials.

cd /d "%~dp0"

if "%MEXC_READONLY_ACCESS_KEY%"=="" goto :missing_access
if "%MEXC_READONLY_SECRET_KEY%"=="" goto :missing_secret
if NOT "%MEXC_READONLY_SCOPE_ATTESTED%"=="1" goto :missing_scope
if NOT "%MEXC_READONLY_RECONCILE_ENABLE%"=="1" goto :missing_reconcile
if NOT "%MEXC_SHADOW_REHEARSAL_ENABLE%"=="1" goto :missing_shadow

if not exist "gate_k_phase_a_evidence" mkdir "gate_k_phase_a_evidence"
set "JOURNAL=%CD%\gate_k_phase_a_evidence\phase_a_campaign.sqlite3"
set "RECEIPT=%CD%\gate_k_phase_a_evidence\latest_cycle_receipt.json"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 -m dream_account.execution_phase_a_campaign_runner --journal "%JOURNAL%" --output "%RECEIPT%"
  set "RC=%ERRORLEVEL%"
  goto :finish
)

where python >nul 2>nul
if %ERRORLEVEL%==0 (
  python -m dream_account.execution_phase_a_campaign_runner --journal "%JOURNAL%" --output "%RECEIPT%"
  set "RC=%ERRORLEVEL%"
  goto :finish
)

echo BLOCKED: Python 3 was not found in PATH.
exit /b 2

:missing_access
echo BLOCKED: MEXC_READONLY_ACCESS_KEY is missing.
exit /b 2
:missing_secret
echo BLOCKED: MEXC_READONLY_SECRET_KEY is missing.
exit /b 2
:missing_scope
echo BLOCKED: MEXC_READONLY_SCOPE_ATTESTED must equal 1.
exit /b 2
:missing_reconcile
echo BLOCKED: MEXC_READONLY_RECONCILE_ENABLE must equal 1.
exit /b 2
:missing_shadow
echo BLOCKED: MEXC_SHADOW_REHEARSAL_ENABLE must equal 1.
exit /b 2

:finish
echo.
if "%RC%"=="0" (
  echo Gate K Phase A cycle completed without a blocking condition.
  echo Journal: %JOURNAL%
  echo Receipt: %RECEIPT%
) else (
  echo Gate K Phase A cycle BLOCKED or failed closed. Exit code: %RC%
)
exit /b %RC%
