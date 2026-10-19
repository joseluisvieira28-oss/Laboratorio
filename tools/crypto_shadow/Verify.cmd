@echo off
cd /d "%~dp0"
if exist "CryptoShadow\CryptoShadow.exe" (
  "CryptoShadow\CryptoShadow.exe" --verify --state "%~dp0state"
) else (
  py -3 shadow.py --verify --state "%~dp0state"
)
pause
