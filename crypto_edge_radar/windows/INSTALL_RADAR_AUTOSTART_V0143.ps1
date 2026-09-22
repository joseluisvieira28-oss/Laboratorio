$ErrorActionPreference = "Stop"
$Watchdog = Join-Path $PSScriptRoot "RUN_RADAR_24X7_V0143.ps1"
if (-not (Test-Path $Watchdog)) { throw "Watchdog script missing: $Watchdog" }

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Watchdog`""
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable
Register-ScheduledTask -TaskName "CryptoEdgeRadarV0143" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Fail-closed Crypto Edge Radar local watchdog" -Force | Out-Null
Write-Host "PASS: CryptoEdgeRadarV0143 starts at logon and restarts after process failure."
