$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$taskName = "CryptoLab-OPTIONS-V21-AutoLive"
Write-Host "=== TASK ==="
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName,State | Format-List
Get-ScheduledTaskInfo -TaskName $taskName | Select-Object LastRunTime,LastTaskResult,NextRunTime | Format-List
Write-Host "=== ENGINE ==="
$statusPath = Join-Path $root "options_v21_autolive_status.json"
if (Test-Path $statusPath) { Get-Content $statusPath -Raw } else { Write-Host "No engine status receipt yet." }
Write-Host "=== CONTROL ==="
Write-Host ("ARMED       : " + (Test-Path (Join-Path $root "AUTO_MICROLIVE_ARMED.json")))
Write-Host ("KILL SWITCH : " + (Test-Path (Join-Path $root "KILL_SWITCH")))
