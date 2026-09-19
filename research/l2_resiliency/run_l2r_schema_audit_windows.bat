@echo off
setlocal EnableExtensions

REM L2-RESILIENCY-001 — frozen full-corpus schema audit launcher.
REM Operational wrapper only. No Discovery, returns, PnL or parameter changes.

if "%~2"=="" (
  echo Usage: %~nx0 "C:\path\to\corpus_root" "C:\path\to\present_manifest.json" ["C:\path\to\output.json"]
  exit /b 2
)

set "CORPUS=%~1"
set "MANIFEST=%~2"
set "OUTPUT=%~3"
if "%OUTPUT%"=="" set "OUTPUT=%CD%\L2_RESILIENCY_001_FULL_CORPUS_SCHEMA_AUDIT_V0_1.json"

if not exist "%CORPUS%" (
  echo FAIL_CLOSED: corpus root not found: %CORPUS%
  exit /b 2
)
if not exist "%MANIFEST%" (
  echo FAIL_CLOSED: manifest not found: %MANIFEST%
  exit /b 2
)

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PY=py -3"
) else (
  where python >nul 2>nul
  if not %ERRORLEVEL%==0 (
    echo FAIL_CLOSED: Python 3 not found.
    exit /b 2
  )
  set "PY=python"
)

%PY% -c "import sys; assert sys.version_info >= (3,10)" >nul 2>nul
if not %ERRORLEVEL%==0 (
  echo FAIL_CLOSED: Python 3.10+ required.
  exit /b 2
)

%PY% -c "import lz4.frame" >nul 2>nul
if not %ERRORLEVEL%==0 (
  echo Installing required source-audit dependency lz4...
  %PY% -m pip install --disable-pip-version-check lz4
  if not %ERRORLEVEL%==0 (
    echo FAIL_CLOSED: could not install lz4.
    exit /b 2
  )
)

set "SCRIPT=%~dp0l2r_full_corpus_schema_audit_v01.py"
if not exist "%SCRIPT%" (
  echo FAIL_CLOSED: frozen audit script missing: %SCRIPT%
  exit /b 2
)

echo ============================================================
echo L2-RESILIENCY-001 SOURCE-SCHEMA AUDIT ONLY
echo Corpus:   %CORPUS%
echo Manifest: %MANIFEST%
echo Output:   %OUTPUT%
echo No signals / no returns / no PnL / no live trading.
echo ============================================================

%PY% "%SCRIPT%" --corpus-root "%CORPUS%" --manifest "%MANIFEST%" --out "%OUTPUT%"
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo FAIL_CLOSED: schema audit did not pass. Receipt: %OUTPUT%
  exit /b %RC%
)

echo.
echo SOURCE_SCHEMA_PASS receipt: %OUTPUT%
exit /b 0
