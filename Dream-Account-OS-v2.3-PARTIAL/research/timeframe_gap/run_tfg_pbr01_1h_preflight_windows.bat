@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
set "REF_FILE=BTC_USDT-Min15-2023-02-01.csv"
set "RAW_DIR="
set "OUTPUT_DIR=%PROJECT_ROOT%\research\local_data\tfg_pbr01_1h_preflight"

echo [TFG-PBR01-1H-001] PRE-OUTCOME ONLY - locating original MEXC corpus...

for /r "%PROJECT_ROOT%\research\local_data" %%F in ("%REF_FILE%") do (
  if /I "%%~nxF"=="%REF_FILE%" if not defined RAW_DIR set "RAW_DIR=%%~dpF"
)

if not defined RAW_DIR (
  for %%D in ("%USERPROFILE%\Desktop" "%USERPROFILE%\Documents" "%USERPROFILE%\Downloads" "%USERPROFILE%\OneDrive") do (
    if exist "%%~D" (
      for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$p=Get-ChildItem -LiteralPath '%%~D' -Filter '%REF_FILE%' -File -Recurse -ErrorAction SilentlyContinue ^| Select-Object -First 1 -ExpandProperty FullName; if($p){$p}"`) do (
        if not defined RAW_DIR set "RAW_DIR=%%~dpF"
      )
    )
  )
)

if not defined RAW_DIR (
  echo BLOCKED_PRE_OUTCOME: exact original MEXC corpus not found.
  echo No signals, outcomes, PnL, 2025, or 2026 data were opened.
  exit /b 2
)

set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"
pushd "%PROJECT_ROOT%" >nul
python -m research.timeframe_gap.timeframe_gap_prefreeze_gate_v01
if errorlevel 1 (
  popd >nul
  echo PREFREEZE GATE FAILED. Nothing executed.
  exit /b 2
)
python -m research.timeframe_gap.tfg_pbr01_1h_preflight_runner_v01 --raw-dir "%RAW_DIR%" --output-dir "%OUTPUT_DIR%"
set "RC=%ERRORLEVEL%"
popd >nul

if not "%RC%"=="0" (
  echo TFG-PBR01-1H-001 preflight BLOCKED or failed closed.
  echo No trade outcome was evaluated.
  exit /b %RC%
)

echo.
echo TFG-PBR01-1H-001 PRE-OUTCOME READY.
echo IMPORTANT: this launcher CANNOT compute performance or unlock 2025/2026.
echo Receipt:
echo   "%OUTPUT_DIR%\TFG_PBR01_1H_PREOUTCOME_PREFLIGHT_V0.1.json"
exit /b 0
