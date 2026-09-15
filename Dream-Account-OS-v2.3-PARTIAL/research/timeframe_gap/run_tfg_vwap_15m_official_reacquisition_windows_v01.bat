@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
set "AMENDMENT=%PROJECT_ROOT%\research\timeframe_gap\TFG_VWAP_15M_001_SOURCE_RECOVERY_AMENDMENT_V0.1.json"
set "RAW_ROOT=%PROJECT_ROOT%\research\local_data\tfg_vwap_15m_reacquired_raw"
set "NORMALIZED_DIR=%PROJECT_ROOT%\research\local_data\tfg_vwap_15m_recovered_normalized"
set "OUTPUT_DIR=%PROJECT_ROOT%\research\local_data\tfg_vwap_15m_source_gate"
set "RECEIPT=%OUTPUT_DIR%\TFG_VWAP_15M_OFFICIAL_REACQUISITION_NORMALIZATION_V0.1.json"

echo ============================================================
echo TFG-VWAP-15M-001 OFFICIAL SOURCE RECOVERY V0.1
echo BINANCE USD-M FUTURES / 2022-2023 ONLY
echo NO VWAP / NO RETURNS / NO PNL / NO 2024 / NO 2025 / NO 2026
echo ============================================================

if not exist "%AMENDMENT%" (
  echo BLOCKED_PRE_OUTCOME: frozen source-recovery amendment is missing.
  exit /b 2
)

python -c "import zstandard" >nul 2>nul
if errorlevel 1 (
  echo BLOCKED_TECHNICAL_PRE_OUTCOME: Python package zstandard is not installed.
  echo Install only the technical dependency with: python -m pip install zstandard
  echo No market archive was downloaded by this launcher.
  exit /b 2
)

set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"
pushd "%PROJECT_ROOT%" >nul
python -m research.timeframe_gap.tfg_vwap_15m_reacquire_and_normalize_v01 --raw-root "%RAW_ROOT%" --normalized-dir "%NORMALIZED_DIR%" --receipt "%RECEIPT%"
set "RC=%ERRORLEVEL%"
popd >nul

if not "%RC%"=="0" (
  echo.
  echo SOURCE RECOVERY DID NOT PASS. Removing any reconstructed normalized packages to prevent accidental reuse.
  if exist "%NORMALIZED_DIR%\H180-0001_NORMALIZED_BTCUSDT.zip" del /q "%NORMALIZED_DIR%\H180-0001_NORMALIZED_BTCUSDT.zip"
  if exist "%NORMALIZED_DIR%\H180-0001_NORMALIZED_ETHUSDT.zip" del /q "%NORMALIZED_DIR%\H180-0001_NORMALIZED_ETHUSDT.zip"
  if exist "%NORMALIZED_DIR%\H180-0001_NORMALIZED_SOLUSDT.zip" del /q "%NORMALIZED_DIR%\H180-0001_NORMALIZED_SOLUSDT.zip"
  if exist "%NORMALIZED_DIR%\H180-0001_NORMALIZED_BNBUSDT.zip" del /q "%NORMALIZED_DIR%\H180-0001_NORMALIZED_BNBUSDT.zip"
  if exist "%NORMALIZED_DIR%\H180-0001_NORMALIZED_XRPUSDT.zip" del /q "%NORMALIZED_DIR%\H180-0001_NORMALIZED_XRPUSDT.zip"
  if exist "%NORMALIZED_DIR%\H180-0001_NORMALIZED_DOGEUSDT.zip" del /q "%NORMALIZED_DIR%\H180-0001_NORMALIZED_DOGEUSDT.zip"
  echo No VWAP signal or trade outcome was evaluated.
  echo Receipt: "%RECEIPT%"
  exit /b %RC%
)

echo.
echo SOURCE RECOVERY + NORMALIZATION PASSED.
echo OUTCOMES ARE STILL LOCKED.
echo The Discovery-only source/member fingerprint must now be committed before any VWAP calculation.
echo Receipt: "%RECEIPT%"
exit /b 0
