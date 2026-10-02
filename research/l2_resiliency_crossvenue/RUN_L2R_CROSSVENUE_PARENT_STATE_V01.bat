@echo off
setlocal
set "RAW=%USERPROFILE%\Desktop\L2R_2024_BTC_BODY_ACQUISITION_LOCAL\HL_L2R_2024_BTC_RAW_V0_1"
set "SCRIPT=%~dp0l2r_crossvenue_parent_state_materializer_v01.py"
echo L2R-CROSSVENUE-001 PARENT STATE MATERIALIZER V0.1
echo RAW=%RAW%
if not exist "%RAW%" (
  echo ERROR: RAW folder not found.
  echo Expected: %RAW%
  exit /b 2
)
python -c "import lz4.frame" >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python package lz4 is missing.
  echo Run: python -m pip install lz4
  exit /b 2
)
python "%SCRIPT%" --raw-root "%RAW%" --workers 4
set RC=%ERRORLEVEL%
echo.
if "%RC%"=="0" (
  echo PASS. Output folder:
  echo %RAW%\_CROSSVENUE_PARENT_STATE_V0_1
) else (
  echo FAIL-CLOSED. Exit code %RC%.
)
exit /b %RC%
