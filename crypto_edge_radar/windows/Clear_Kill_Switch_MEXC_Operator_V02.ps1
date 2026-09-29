$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\OperatorFuturesV02"
$killPath = Join-Path $runtime "OPERATOR_FUTURES_V02_KILL_SWITCH"
$statePath = Join-Path $runtime "live_state\operator_futures_engine_v02.json"
if (Test-Path -LiteralPath $statePath) {
    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    if ($state.status -notin @("IDLE_NO_OPERATOR_POSITION","CLOSED_RECONCILED","WATCHING_FOR_BNB_LAUNCHPOOL_EVENT")) { throw "Refusing to clear kill switch while operator state is not safely idle/closed." }
}
if (Test-Path -LiteralPath $killPath) { Remove-Item -LiteralPath $killPath -Force }
Write-Host "KILL SWITCH:" (Test-Path -LiteralPath $killPath)
