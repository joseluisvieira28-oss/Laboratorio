@echo off
chcp 65001 >nul
powershell.exe -NoProfile -File "%~dp0scripts\Activate.ps1"
echo.
pause