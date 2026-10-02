$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV04"
$stateDir = Join-Path $runtime "live_state"
$armed = Join-Path $runtime "OPERATOR_FUTURES_V04_ARMED.json"
$kill = Join-Path $runtime "OPERATOR_FUTURES_V04_KILL_SWITCH"
$authority = Join-Path $runtime "OPERATOR_FUTURES_GLOBAL_AUTHORITY_V04_ACTIVE.json"
$ledger = Join-Path $stateDir "MULTI_SLOT_LEDGER_V04.json"

Write-Host "=== V0.4 CONTROL ==="
Write-Host ("ACTIVE AUTHORITY : " + (Test-Path -LiteralPath $authority))
Write-Host ("ARMED            : " + (Test-Path -LiteralPath $armed))
Write-Host ("KILL SWITCH      : " + (Test-Path -LiteralPath $kill))
Write-Host ("LEDGER           : " + (Test-Path -LiteralPath $ledger))

foreach ($name in @("triple_ready_v04.json","triple_fishing_operator_v04.json","operator_futures_engine_v04.json","MULTI_SLOT_LEDGER_V04.json")) {
    $p=Join-Path $stateDir $name
    if (Test-Path -LiteralPath $p) {
        Write-Host ""
        Write-Host ("=== " + $name + " ===")
        Get-Content -Raw -LiteralPath $p
    }
}
