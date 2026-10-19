@echo off
setlocal EnableExtensions

set "ROOT=%LOCALAPPDATA%\MRCR\h02_frozen_scope_shadow_v01"
set "PY=%ROOT%\venv\Scripts\python.exe"
set "DB=%ROOT%\data\h02_frozen_scope_shadow.sqlite3"
set "VERIFY=%~dp0verify_h02_frozen_scope_shadow.py"

if not exist "%PY%" (
  echo MRCR H02 VERIFY: FAIL-CLOSED - local venv not found
  exit /b 2
)
if not exist "%DB%" (
  echo MRCR H02 VERIFY: FAIL-CLOSED - local journal not found
  exit /b 2
)

"%PY%" "%VERIFY%" --db "%DB%"
exit /b %ERRORLEVEL%
