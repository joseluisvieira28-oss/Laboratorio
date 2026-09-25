$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$taskName = "CryptoLab-OPTIONS-V21-Futures-AutoLive"
$armed = Join-Path $root "AUTO_MICROLIVE_FUTURES_ARMED.json"
if (Test-Path $armed) { Remove-Item $armed -Force }
Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
Write-Host "OPTIONS V2.1 Futures Auto-Live DISARMED. No new entries can occur."
