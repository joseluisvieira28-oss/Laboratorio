@echo off
setlocal EnableExtensions

set "ROOT=%LOCALAPPDATA%\MRCR\h02_frozen_scope_shadow_v01"
set "VENV=%ROOT%\venv"
set "DATA=%ROOT%\data"
set "DB=%DATA%\h02_frozen_scope_shadow.sqlite3"
set "PY=%VENV%\Scripts\python.exe"
set "SCRIPT=%~dp0h02_frozen_scope_shadow_collector.py"
set "VERIFY=%~dp0verify_h02_frozen_scope_shadow.py"
set "SECONDS=60"

if not "%MRCR_H02_SHADOW_SECONDS%"=="" set "SECONDS=%MRCR_H02_SHADOW_SECONDS%"

if not exist "%SCRIPT%" (
  echo MRCR H02 SHADOW: FAIL-CLOSED - collector script not found
  exit /b 2
)
if not exist "%VERIFY%" (
  echo MRCR H02 SHADOW: FAIL-CLOSED - verifier script not found
  exit /b 2
)
if not exist "%DATA%" mkdir "%DATA%"

if not exist "%PY%" (
  where py >nul 2>nul
  if errorlevel 1 (
    echo MRCR H02 SHADOW: FAIL-CLOSED - Python launcher not found
    exit /b 2
  )
  if not exist "%ROOT%" mkdir "%ROOT%"
  py -3 -m venv "%VENV%"
  if errorlevel 1 exit /b 2
)

"%PY%" -m pip install --disable-pip-version-check websockets==15.0.1
if errorlevel 1 exit /b 2

echo.
echo MRCR H02 Frozen-Scope Shadow Collector
echo Source infrastructure only / public data / local raw journal
echo Scope: BTC+ETH x Binance Spot+Coinbase Advanced Spot
echo Duration: %SECONDS% seconds
echo.

"%PY%" "%SCRIPT%" --seconds %SECONDS% --db "%DB%"
set "COLLECT_RC=%ERRORLEVEL%"

echo.
echo Independent offline restart/recovery verification:
"%PY%" "%VERIFY%" --db "%DB%"
set "VERIFY_RC=%ERRORLEVEL%"

if "%COLLECT_RC%"=="0" if "%VERIFY_RC%"=="0" (
  echo.
  echo MRCR H02 FROZEN-SCOPE SHADOW: PASS
  exit /b 0
)

echo.
echo MRCR H02 FROZEN-SCOPE SHADOW: FAIL-CLOSED
exit /b 2
