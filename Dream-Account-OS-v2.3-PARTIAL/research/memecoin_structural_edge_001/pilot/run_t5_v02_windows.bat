@echo off
setlocal

REM MSEL-001 — T+5 V0.2 fail-closed launcher
REM READ-ONLY / RESEARCH-ONLY / OUTCOMES LOCKED

cd /d "%~dp0"

if "%HELIUS_API_KEY%"=="" if "%MSEL_RPC_URL%"=="" (
  echo FAIL-CLOSED: HELIUS_API_KEY or MSEL_RPC_URL is not set in this terminal.
  echo Set the credential privately, then rerun this file. Do not paste the key into chat or commit it.
  exit /b 2
)

echo [1/3] Compiling V0.1 base, V0.2 correction and synthetic guard...
python -m py_compile collect_t5_forensics_blockscan_free.py collect_t5_forensics_blockscan_free_v02.py test_t5_accountmap_v02.py
if errorlevel 1 exit /b %errorlevel%

echo [2/3] Running historical 2025 Pump account-map guard...
python test_t5_accountmap_v02.py
if errorlevel 1 exit /b %errorlevel%

echo [3/3] Running T+1/T+3/T+5 forensic reconstruction V0.2...
python collect_t5_forensics_blockscan_free_v02.py
if errorlevel 1 exit /b %errorlevel%

echo.
echo PASS: MSEL-001 T+5 V0.2 execution finished.
echo OUTCOMES REMAIN LOCKED.
exit /b 0
