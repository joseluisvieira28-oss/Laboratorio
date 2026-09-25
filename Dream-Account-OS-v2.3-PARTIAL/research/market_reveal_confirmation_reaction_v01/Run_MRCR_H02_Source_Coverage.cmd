@echo off
setlocal EnableExtensions

set "ROOT=%LOCALAPPDATA%\MRCR\h02_source_coverage_v01"
set "VENV=%ROOT%\venv"
set "PY=%VENV%\Scripts\python.exe"
set "SCRIPT=%~dp0h02_source_coverage_probe.py"

if not exist "%SCRIPT%" (
  echo H02 SOURCE COVERAGE: FAIL-CLOSED - probe script not found
  exit /b 2
)

if not exist "%PY%" (
  where py >nul 2>nul
  if errorlevel 1 (
    echo H02 SOURCE COVERAGE: FAIL-CLOSED - Python launcher not found
    exit /b 2
  )
  if not exist "%ROOT%" mkdir "%ROOT%"
  py -3 -m venv "%VENV%"
  if errorlevel 1 exit /b 2
)

"%PY%" -m pip install --disable-pip-version-check websockets==15.0.1
if errorlevel 1 exit /b 2

echo.
echo MRCR H02 Exact Source Coverage Probe
echo Public market data only / no auth / no raw persistence / no outcomes
echo Frozen scope: BTC+ETH x Binance Spot+Coinbase Advanced Spot
echo.

"%PY%" "%SCRIPT%" --seconds 12
set "RC=%ERRORLEVEL%"

if "%RC%"=="0" (
  echo.
  echo H02 SOURCE COVERAGE: PASS
) else (
  echo.
  echo H02 SOURCE COVERAGE: FAIL-CLOSED ^(exit %RC%^)
)

exit /b %RC%
