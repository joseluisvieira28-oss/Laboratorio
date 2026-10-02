$ErrorActionPreference = "Stop"
$taskName = "CryptoLab-Triple-Fishing-Operator-V04"
$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV04"
$stateDir = Join-Path $runtime "live_state"
$ledger = Join-Path $stateDir "MULTI_SLOT_LEDGER_V04.json"
$armed = Join-Path $runtime "OPERATOR_FUTURES_V04_ARMED.json"

if (Test-Path -LiteralPath $ledger) {
    $l = Get-Content -Raw -LiteralPath $ledger | ConvertFrom-Json
    $count = @($l.reservations).Count
    if ($count -gt 0) { throw ("Refusing to disarm: " + $count + " reservation(s) still active or unresolved.") }
}
Remove-Item -LiteralPath $armed -Force -ErrorAction SilentlyContinue
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($null -ne $task) { Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue }
Write-Host "V0.4 disarmed only after an empty reservation ledger."
