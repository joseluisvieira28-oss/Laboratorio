$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Launcher = Join-Path $PSScriptRoot "START_RADAR_RECOVERY_V0141.ps1"
$WatchdogLog = Join-Path $Root "logs\radar_watchdog.log"
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $WatchdogLog) | Out-Null

$Mutex = New-Object System.Threading.Mutex($false, "Local\CryptoEdgeRadarV0143Watchdog")
if (-not $Mutex.WaitOne(0)) {
    Write-Host "Radar watchdog is already running."
    exit 0
}

$env:RADAR_NO_BROWSER = "1"
while ($true) {
    try {
        & $Launcher *>> $WatchdogLog
    }
    catch {
        "$(Get-Date -Format o) WATCHDOG_RESTART_FAILED $($_.Exception.Message)" | Add-Content $WatchdogLog
    }
    Start-Sleep -Seconds 15
}
