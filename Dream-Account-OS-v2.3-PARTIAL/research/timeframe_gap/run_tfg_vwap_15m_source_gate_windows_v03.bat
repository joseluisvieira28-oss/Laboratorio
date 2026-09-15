@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "PROJECT_ROOT=%%~fI"
set "OUTPUT_DIR=%PROJECT_ROOT%\research\local_data\tfg_vwap_15m_source_gate"
set "FREEZE=%PROJECT_ROOT%\research\timeframe_gap\TFG_VWAP_15M_001_FREEZE.json"
set "AMENDMENT=%PROJECT_ROOT%\research\timeframe_gap\TFG_VWAP_PROVENANCE_AMENDMENT_01.json"
set "ACTIVATION=%PROJECT_ROOT%\research\timeframe_gap\TFG_VWAP_15M_001_ACTIVATION_V0.1.json"
set "RECEIPT=%OUTPUT_DIR%\TFG_VWAP_15M_SOURCE_BYTE_GATE_V0.1.json"
set "NORMALIZED_DIR="

echo ============================================================
echo TFG-VWAP-15M-001 SOURCE BYTE GATE V0.3
echo OUTCOME-BLIND / NO PNL / NO 2024 / NO 2025 / NO 2026
echo ============================================================

set "PYTHONPATH=%PROJECT_ROOT%\src;%PROJECT_ROOT%;%PYTHONPATH%"

if not "%~1"=="" (
  for /f "usebackq delims=" %%F in (`python -m research.timeframe_gap.locate_h180_normalized_packages_v01 --project-root "%PROJECT_ROOT%" --candidate "%~1" 2^>nul`) do if not defined NORMALIZED_DIR set "NORMALIZED_DIR=%%F"
) else (
  for /f "usebackq delims=" %%F in (`python -m research.timeframe_gap.locate_h180_normalized_packages_v01 --project-root "%PROJECT_ROOT%" 2^>nul`) do if not defined NORMALIZED_DIR set "NORMALIZED_DIR=%%F"
)

if not defined NORMALIZED_DIR (
  echo BLOCKED_PRE_OUTCOME_SOURCE_GATE: no directory containing all 6 H180 normalized ZIP packages was found.
  echo No ZIP member was opened. No market row was parsed. No outcome was evaluated.
  exit /b 2
)

echo Found VERIFIED 6-package H180 directory:
echo   %NORMALIZED_DIR%
echo.

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
echo Receipt:
echo   "%RECEIPT%"
exit /b 0
