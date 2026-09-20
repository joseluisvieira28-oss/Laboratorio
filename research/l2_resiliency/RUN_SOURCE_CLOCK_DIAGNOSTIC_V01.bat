@echo off
setlocal
echo ============================================================
echo L2-RESILIENCY-001 - SOURCE CLOCK DIAGNOSTIC V0.1
echo TIMESTAMPS ONLY - NO PRICES / NO OUTCOMES / NO PNL
echo ============================================================
echo.
set "BASE=%USERPROFILE%\Desktop\L2R_2025_BTC_VALIDATION_LOCAL"
set "SCRIPT=%~dp0l2r_2025_source_clock_diagnostic_v01.py"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
  py -3 "%SCRIPT%" --base "%BASE%"
) else (
  python "%SCRIPT%" --base "%BASE%"
)
if not %ERRORLEVEL%==0 (
  echo.
  echo DIAGNOSTIC FAILED CLOSED.
  pause
  exit /b 1
)
echo.
echo DONE.
echo Upload ONLY:
echo %BASE%\L2_RESILIENCY_001_2025_SOURCE_CLOCK_DIAGNOSTIC_V0_1.zip
pause
