@echo off
chcp 65001 >nul
powershell.exe -NoProfile -File "%~dp0scripts\Status.ps1"
echo.
pause