@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "REF_FILE=BTC_USDT-Min15-2023-02-01.csv"
set "RAW_DIR="
set "OUTPUT_DIR=%PROJECT_ROOT%\research\local_data\tfg_pbr01_4h"

echo [TFG-PBR01-4H-001] Locating original MEXC corpus...

for /r "%PROJECT_ROOT%\research\local_data" %%F in ("%REF_FILE%") do (
  if exist "%%~fF" if /I "%%~nxF"=="%REF_FILE%" if not defined RAW_DIR set "RAW_DIR=%%~dpF"
)

if not defined RAW_DIR (
  for %%D in ("%USERPROFILE%\Desktop" "%USERPROFILE%\Documents" "%USERPROFILE%\Downloads" "%USERPROFILE%\OneDrive") do (
    if exist "%%~D" (
      for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$p=Get-ChildItem -LiteralPath '%%~D' -Filter '%REF_FILE%' -File -Recurse -ErrorAction SilentlyContinue ^| Select-Object -First 1 -ExpandProperty FullName; if($p){$p}"`) do (
        if exist "%%~fF" if not defined RAW_DIR set "RAW_DIR=%%~dpF"
      )
    )
  )
)

if not defined RAW_DIR (
  echo.
  echo BLOCKED_PRE_OUTCOME: original MEXC corpus was not found.
  echo Expected reference file: %REF_FILE%
  echo No outcome was inspected. No 2025/2026 data was accessed.
  exit /b 2
)

if "%RAW_DIR:~-1%"=="\" set "RAW_DIR=%RAW_DIR:~0,-1%"

echo Found corpus candidate:
echo   %RAW_DIR%
echo.

set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"
pushd "%PROJECT_ROOT%" >nul
python -m research.tfg_pbr01_4h_local_orchestrator_v01 --raw-dir "%RAW_DIR%" --output-dir "%OUTPUT_DIR%"
set "RC=%ERRORLEVEL%"
popd >nul

if not "%RC%"=="0" (
  echo.
  echo TFG-PBR01-4H-001 BLOCKED or failed closed.
  echo No 2025/2026 data access, exchange mutation, order, or live trading was performed.
  echo Preflight receipt:
  echo   "%OUTPUT_DIR%\TFG_PBR01_4H_LOCAL_PREFLIGHT_V0.1.json"
  exit /b %RC%
)

echo.
echo TFG-PBR01-4H-001 DISCOVERY COMPLETE.
echo Receipt:
echo   "%OUTPUT_DIR%\TFG_PBR01_4H_DISCOVERY_RECEIPT_V0.1.json"
echo Ledger:
echo   "%OUTPUT_DIR%\TFG_PBR01_4H_DISCOVERY_LEDGER_V0.1.json"
echo.
echo Validation remains LOCKED. 2026 remains LOCKED.
exit /b 0
