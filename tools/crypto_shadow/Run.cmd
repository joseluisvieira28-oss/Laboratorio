@echo off
cd /d "%~dp0"
if exist "CryptoShadow\CryptoShadow.exe" (
  "CryptoShadow\CryptoShadow.exe" --state "%~dp0state"
) else (
  py -3 shadow.py --state "%~dp0state"
)
pause
