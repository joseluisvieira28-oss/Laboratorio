@echo off
chcp 65001 >nul
powershell.exe -NoProfile -File "%~dp0scripts\Stop-New-Entries.ps1"
echo.
pause