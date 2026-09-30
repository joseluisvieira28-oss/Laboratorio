$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV03"
$stateDir = Join-Path $runtime "live_state"
$armed = Join-Path $runtime "OPERATOR_FUTURES_V03_ARMED.json"
$kill = Join-Path $runtime "OPERATOR_FUTURES_V03_KILL_SWITCH"
$slot = Join-Path $stateDir "GLOBAL_POSITION_SLOT_V03.json"

Write-Host "=== CONTROL ==="
Write-Host ("ARMED       : " + (Test-Path -LiteralPath $armed))
Write-Host ("KILL SWITCH : " + (Test-Path -LiteralPath $kill))
Write-Host ("GLOBAL SLOT : " + (Test-Path -LiteralPath $slot))

Write-Host ""
Write-Host "=== TASK ==="
Get-ScheduledTask -TaskName "CryptoLab-Triple-Fishing-Operator-V03" -ErrorAction SilentlyContinue | Select-Object TaskName,State
Get-ScheduledTaskInfo -TaskName "CryptoLab-Triple-Fishing-Operator-V03" -ErrorAction SilentlyContinue | Select-Object LastRunTime,LastTaskResult,NextRunTime

foreach ($name in @("triple_ready_v03.json","triple_fishing_operator_v03.json","operator_futures_engine_v03.json","GLOBAL_POSITION_SLOT_V03.json")) {
    $p=Join-Path $stateDir $name
    if (Test-Path -LiteralPath $p) {
        Write-Host ""
        Write-Host ("=== " + $name + " ===")
        Get-Content -Raw -LiteralPath $p
    }
}
