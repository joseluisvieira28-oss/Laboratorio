@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "VENV=%TEMP%\mrcr_coinbase_l2_probe_v01"

where py >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python launcher "py" was not found.
  exit /b 10
)

if not exist "%VENV%\Scripts\python.exe" (
  py -3 -m venv "%VENV%"
  if errorlevel 1 exit /b 11
)

call "%VENV%\Scripts\activate.bat"
if errorlevel 1 exit /b 12

python -m pip install --disable-pip-version-check --no-input websockets==15.0.1
if errorlevel 1 exit /b 13

python "%SCRIPT_DIR%coinbase_level2_local_probe.py" --seconds 12
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
  echo MRCR Coinbase L2 source probe: PASS
) else (
  echo MRCR Coinbase L2 source probe: FAIL/BLOCKED ^(exit %RC%^)
)

exit /b %RC%
