@echo off
setlocal
cd /d "%~dp0\.."

echo ============================================================
echo DERIVATIVES POSITIONING - PHASE 0E SCHEMA INVENTORY
echo ============================================================
echo Header/schema only. No outcomes. No 2025. No 2026.
echo.

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 research\derivatives_positioning_phase0e_schema_inventory_v01.py
) else (
  where python >nul 2>nul
  if not %errorlevel%==0 (
    echo FAIL-CLOSED: Python 3 was not found.
    exit /b 1
  )
  python research\derivatives_positioning_phase0e_schema_inventory_v01.py
)

set RC=%errorlevel%
echo.
if %RC%==0 (
  echo PHASE 0E COMPLETED: PASS
) else (
  echo PHASE 0E STOPPED FAIL-CLOSED. Exit code: %RC%
)
echo Receipt:
echo   C:\Users\José\Desktop\DERIVATIVES_POSITIONING_DATA_V0.1\AUDIT\DP_PHASE0E_SCHEMA_INVENTORY_RECEIPT.json
exit /b %RC%
