@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem TFG VWAP provenance-only preflight. NO VWAP, signals, returns, PnL or outcomes.
set "SCRIPT_DIR=%~dp0"
set "NORMALIZED_DIR="
set "PROVENANCE_MANIFEST="
set "RECEIPT_DIR=%SCRIPT_DIR%receipts"
set "RECEIPT=%RECEIPT_DIR%\TFG_VWAP_DISCOVERY_PROVENANCE_PREFLIGHT_V0.1.json"
set "STATIC_RECEIPT=%RECEIPT_DIR%\TFG_VWAP_PROVENANCE_STATIC_GATE_V0.1.json"

if not exist "%RECEIPT_DIR%" mkdir "%RECEIPT_DIR%"

echo [TFG VWAP] PROVENANCE-ONLY PREFLIGHT. No outcomes are authorized.

for %%D in ("%USERPROFILE%\Desktop" "%USERPROFILE%\Documents" "%USERPROFILE%\Downloads" "%USERPROFILE%\OneDrive") do (
  if exist "%%~D" if not defined PROVENANCE_MANIFEST (
    for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$p=Get-ChildItem -LiteralPath '%%~D' -Filter 'H180-0001_PROVENANCE_MANIFEST.json' -File -Recurse -ErrorAction SilentlyContinue ^| Select-Object -First 1 -ExpandProperty FullName; if($p){$p}"`) do set "PROVENANCE_MANIFEST=%%~fF"
  )
)

if not defined PROVENANCE_MANIFEST (
  echo BLOCKED_PROVENANCE: H180-0001_PROVENANCE_MANIFEST.json not found.
  exit /b 2
)

for %%D in ("%USERPROFILE%\Desktop" "%USERPROFILE%\Documents" "%USERPROFILE%\Downloads" "%USERPROFILE%\OneDrive") do (
  if exist "%%~D" if not defined NORMALIZED_DIR (
    for /f "usebackq delims=" %%F in (`powershell -NoProfile -Command "$p=Get-ChildItem -LiteralPath '%%~D' -Filter 'H180-0001_NORMALIZED_BTCUSDT.zip' -File -Recurse -ErrorAction SilentlyContinue ^| Select-Object -First 1 -ExpandProperty FullName; if($p){$p}"`) do set "NORMALIZED_DIR=%%~dpF"
  )
)

if not defined NORMALIZED_DIR (
  echo BLOCKED_PROVENANCE: normalized H180 package directory not found.
  exit /b 2
)

python "%SCRIPT_DIR%tfg_vwap_provenance_static_gate_v01.py" "%SCRIPT_DIR%tfg_vwap_provenance_preflight_v01.py" --receipt "%STATIC_RECEIPT%"
if errorlevel 1 (
  echo BLOCKED_STATIC_GATE. No market package was opened.
  exit /b 2
)

python "%SCRIPT_DIR%tfg_vwap_provenance_preflight_v01.py" --normalized-dir "%NORMALIZED_DIR%" --provenance-manifest "%PROVENANCE_MANIFEST%" --receipt "%RECEIPT%"
set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo TFG VWAP provenance preflight BLOCKED. No outcomes were evaluated.
  exit /b %RC%
)

echo PASS_DISCOVERY_SOURCE_IDENTITY_ONLY.
echo This does NOT authorize VWAP outcomes or protected-period access.
echo Receipt: "%RECEIPT%"
exit /b 0
