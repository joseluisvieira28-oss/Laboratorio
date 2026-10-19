@echo off
cd /d "%~dp0"
if exist "CryptoShadow\CryptoShadow.exe" (
  "CryptoShadow\CryptoShadow.exe" --once --state "%~dp0smoke-state"
) else (
  py -3 shadow.py --once --state "%~dp0smoke-state"
)
echo Ver o painel em smoke-state\painel.html. NO-GO nao significa falha tecnica.
pause
