@echo off
setlocal
cd /d "%~dp0.."

if "%RADAR_DATABASE_URL%"=="" (
  echo [FAIL_CLOSED] RADAR_DATABASE_URL is not configured in this Windows environment.
  echo No process was started. Do NOT paste credentials into this BAT file.
  exit /b 2
)

where py >nul 2>nul
if errorlevel 1 (
  echo [FAIL_CLOSED] Python launcher 'py' was not found.
  exit /b 3
)

if not exist ".venv\Scripts\python.exe" (
  echo Creating local virtual environment...
  py -3.12 -m venv .venv
  if errorlevel 1 exit /b 4
)

call ".venv\Scripts\activate.bat"
python -m pip install -e .
if errorlevel 1 exit /b 5

echo Starting CRYPTO EDGE RADAR forward loop.
echo Public/read-only shadow only. No HTTP server. No orders. Ctrl+C to stop.
python -m radar forward-loop --interval 30
exit /b %ERRORLEVEL%
