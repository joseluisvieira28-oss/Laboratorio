@echo off
setlocal
cd /d "%~dp0.."

echo ============================================================
echo CROSS-VENUE FUNDING/BASIS V0.4.4 - OFFICIAL ARCHIVE ATTACK
echo ============================================================
echo.
echo Provenance only. No trading. No 2026. No PnL output.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_cross_venue_funding_basis_v044_windows.ps1" -Stage ALL
set "EXITCODE=%ERRORLEVEL%"

echo.
if "%EXITCODE%"=="0" (
  echo V0.4.4 runner completed with PASS exit code.
) else (
  echo V0.4.4 runner stopped fail-closed. Exit code: %EXITCODE%
)
echo.
echo Final receipts, when produced, are under:
echo   v044_asset_ctx_work\final_receipts

echo.
pause
exit /b %EXITCODE%
