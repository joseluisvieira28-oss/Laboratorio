$ErrorActionPreference = "Stop"
$Watchdog = Join-Path $PSScriptRoot "RUN_RADAR_24X7_V0144.ps1"
if (-not (Test-Path $Watchdog)) { throw "Watchdog script missing: $Watchdog" }

# V0.14.4 supersedes the V0.14.3 watchdog task. Remove only the known Radar
# task name; never touch unrelated scheduled tasks.
$OldTask = Get-ScheduledTask -TaskName "CryptoEdgeRadarV0143" -ErrorAction SilentlyContinue
if ($null -ne $OldTask) {
    Stop-ScheduledTask -TaskName "CryptoEdgeRadarV0143" -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName "CryptoEdgeRadarV0143" -Confirm:$false
}

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Watchdog`""
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable
Register-ScheduledTask -TaskName "CryptoEdgeRadarV0144" -Action $Action -Trigger $Trigger -Settings $Settings -Description "Fail-closed Crypto Edge Radar V0.14.4 eight-motor local watchdog" -Force | Out-Null
Write-Host "PASS: CryptoEdgeRadarV0144 starts at logon and restarts after process failure."
