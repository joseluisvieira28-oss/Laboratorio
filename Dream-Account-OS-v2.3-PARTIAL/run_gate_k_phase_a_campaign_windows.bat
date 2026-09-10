@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Gate K Phase A — bounded local campaign launcher
REM SHADOW / READ-ONLY only. This file never contains credentials.
REM Usage: run_gate_k_phase_a_campaign_windows.bat <cycles 1-20> <interval_seconds 120-21600>

cd /d "%~dp0"

if "%~1"=="" goto :usage
if "%~2"=="" goto :usage

if "%MEXC_READONLY_ACCESS_KEY%"=="" goto :missing_access
if "%MEXC_READONLY_SECRET_KEY%"=="" goto :missing_secret
if NOT "%MEXC_READONLY_SCOPE_ATTESTED%"=="1" goto :missing_scope
if NOT "%MEXC_READONLY_RECONCILE_ENABLE%"=="1" goto :missing_reconcile
if NOT "%MEXC_SHADOW_REHEARSAL_ENABLE%"=="1" goto :missing_shadow

if defined PYTHONPATH (
  set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
) else (
  set "PYTHONPATH=%CD%\src"
)

if not exist "gate_k_phase_a_evidence" mkdir "gate_k_phase_a_evidence"
set "JOURNAL=%CD%\gate_k_phase_a_evidence\phase_a_campaign.sqlite3"
set "LATEST_CYCLE=%CD%\gate_k_phase_a_evidence\latest_cycle_receipt.json"
set "BATCH_RECEIPT=%CD%\gate_k_phase_a_evidence\latest_campaign_batch_receipt.json"
set "CYCLES=%~1"
set "INTERVAL=%~2"

where py >nul 2>nul
if !ERRORLEVEL!==0 goto :run_py

where python >nul 2>nul
if !ERRORLEVEL!==0 goto :run_python

echo BLOCKED: Python 3 was not found in PATH.
exit /b 2

:run_py
py -3 -m dream_account.execution_phase_a_campaign_batch --journal "%JOURNAL%" --cycles "%CYCLES%" --interval-seconds "%INTERVAL%" --latest-cycle-output "%LATEST_CYCLE%" --output "%BATCH_RECEIPT%"
set "RC=!ERRORLEVEL!"
goto :finish

:run_python
python -m dream_account.execution_phase_a_campaign_batch --journal "%JOURNAL%" --cycles "%CYCLES%" --interval-seconds "%INTERVAL%" --latest-cycle-output "%LATEST_CYCLE%" --output "%BATCH_RECEIPT%"
set "RC=!ERRORLEVEL!"
goto :finish

:usage
echo BLOCKED: explicit campaign parameters are required.
echo Usage: %~nx0 ^<cycles 1-20^> ^<interval_seconds 120-21600^>
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
if "!RC!"=="0" (
  echo Gate K Phase A controlled batch completed without a blocking condition.
  echo Journal: %JOURNAL%
  echo Latest cycle receipt: %LATEST_CYCLE%
  echo Batch receipt: %BATCH_RECEIPT%
) else (
  echo Gate K Phase A controlled batch BLOCKED, interrupted, or failed closed. Exit code: !RC!
)
exit /b !RC!
