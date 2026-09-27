@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "ROOT=%LOCALAPPDATA%\MRCR\shadow_v01"
set "VENV=%ROOT%\venv"
set "DB=%ROOT%\data\coinbase_l2_shadow.sqlite3"

if not exist "%VENV%\Scripts\python.exe" (
  echo ERROR: shadow collector virtual environment not found.
  echo Run Run_MRCR_Coinbase_L2_Shadow.cmd first.
  exit /b 10
)

if not exist "%DB%" (
  echo ERROR: local shadow journal not found:
  echo %DB%
  exit /b 11
)

call "%VENV%\Scripts\activate.bat"
if errorlevel 1 exit /b 12

python "%SCRIPT_DIR%verify_shadow_journal.py" --db "%DB%"
exit /b %ERRORLEVEL%
