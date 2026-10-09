@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "ROOT=%LOCALAPPDATA%\MRCR\shadow_v01"
set "VENV=%ROOT%\venv"
set "DATA=%ROOT%\data"
set "DB=%DATA%\coinbase_l2_shadow.sqlite3"

if not exist "%DATA%" mkdir "%DATA%"

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

echo.
echo MRCR Coinbase L2 Shadow Collector
echo Source-only / non-target / public market data
echo Local journal: %DB%
echo.

python "%SCRIPT_DIR%coinbase_l2_shadow_collector.py" --product BTC-USD --seconds 60 --db "%DB%"
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
  echo SHADOW COLLECTOR: PASS
) else (
  echo SHADOW COLLECTOR: FAIL-CLOSED ^(exit %RC%^)
)

echo.
echo Running offline journal verification...
python "%SCRIPT_DIR%verify_shadow_journal.py" --db "%DB%"
set "VERIFY_RC=%ERRORLEVEL%"

if not "%VERIFY_RC%"=="0" (
  exit /b %VERIFY_RC%
)

exit /b %RC%
