@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
set "REF_PACKAGE=H180-0001_NORMALIZED_BTCUSDT.zip"
set "NORMALIZED_DIR="
set "OUTPUT_DIR=%PROJECT_ROOT%\research\local_data\tfg_vwap_15m_source_gate"
set "FREEZE=%PROJECT_ROOT%\research\timeframe_gap\TFG_VWAP_15M_001_FREEZE.json"
set "AMENDMENT=%PROJECT_ROOT%\research\timeframe_gap\TFG_VWAP_PROVENANCE_AMENDMENT_01.json"
set "ACTIVATION=%PROJECT_ROOT%\research\timeframe_gap\TFG_VWAP_15M_001_ACTIVATION_V0.1.json"
set "RECEIPT=%OUTPUT_DIR%\TFG_VWAP_15M_SOURCE_BYTE_GATE_V0.1.json"

echo ============================================================
echo TFG-VWAP-15M-001 SOURCE BYTE GATE V0.1
echo OUTCOME-BLIND / NO PNL / NO 2024 / NO 2025 / NO 2026
echo ============================================================

if not "%~1"=="" (
  if exist "%~1\%REF_PACKAGE%" set "NORMALIZED_DIR=%~1"
)

if not defined NORMALIZED_DIR (
  for /r "%PROJECT_ROOT%\research\local_data" %%F in ("%REF_PACKAGE%") do (
    if exist "%%~fF" if /I "%%~nxF"=="%REF_PACKAGE%" if not defined NORMALIZED_DIR set "NORMALIZED_DIR=%%~dpF"
  )
)

if not defined NORMALIZED_DIR (
  for %%D in ("%USERPROFILE%\Desktop" "%USERPROFILE%\Documents" "%USERPROFILE%\Downloads" "%USERPROFILE%\OneDrive") do (
    if exist "%%~D" (
      for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$p=Get-ChildItem -LiteralPath '%%~D' -Filter '%REF_PACKAGE%' -File -Recurse -ErrorAction SilentlyContinue ^| Select-Object -First 1 -ExpandProperty DirectoryName; if($p){$p}"`) do (
        if not defined NORMALIZED_DIR set "NORMALIZED_DIR=%%~F"
      )
    )
  )
)

if not defined NORMALIZED_DIR (
  echo BLOCKED_PRE_OUTCOME_SOURCE_GATE: H180 normalized package directory not found.
  echo Expected reference package: %REF_PACKAGE%
  echo No market member was opened. No outcome was evaluated.
  exit /b 2
)

for %%S in (BTCUSDT ETHUSDT SOLUSDT BNBUSDT XRPUSDT DOGEUSDT) do (
  if not exist "%NORMALIZED_DIR%\H180-0001_NORMALIZED_%%S.zip" (
    echo BLOCKED_PRE_OUTCOME_SOURCE_GATE: missing H180-0001_NORMALIZED_%%S.zip
    exit /b 2
  )
)

if "%NORMALIZED_DIR:~-1%"=="\" set "NORMALIZED_DIR=%NORMALIZED_DIR:~0,-1%"

echo Found H180 normalized package directory:
echo   %NORMALIZED_DIR%
echo.

set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"
pushd "%PROJECT_ROOT%" >nul
python -m research.timeframe_gap.tfg_vwap_15m_source_gate_v01 --normalized-dir "%NORMALIZED_DIR%" --freeze "%FREEZE%" --amendment "%AMENDMENT%" --activation "%ACTIVATION%" --receipt "%RECEIPT%"
set "RC=%ERRORLEVEL%"
popd >nul

if not "%RC%"=="0" (
  echo.
  echo TFG-VWAP-15M-001 SOURCE GATE BLOCKED.
  echo No trade outcome, 2024, 2025, or 2026 member was opened.
  exit /b %RC%
)

echo.
echo SOURCE BYTE GATE PASSED.
echo IMPORTANT: OUTCOMES ARE STILL LOCKED.
echo Commit discovery_member_fingerprint before Discovery execution.
echo Receipt:
echo   "%RECEIPT%"
exit /b 0
