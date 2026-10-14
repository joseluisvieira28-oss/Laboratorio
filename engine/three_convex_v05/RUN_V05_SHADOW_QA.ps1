# Offline QA only. No MEXC credentials, exchange calls, orders, service install or arming.
$ErrorActionPreference = "Stop"
Push-Location -LiteralPath $PSScriptRoot
try {
    $python = (Get-Command py -ErrorAction SilentlyContinue)
    if ($null -ne $python) {
        $runner = "py"
        $pyArgs = @("-3")
    } else {
        $python = Get-Command python -ErrorAction Stop
        $runner = "python"
        $pyArgs = @()
    }
    $id = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")
    $dest = Join-Path $PSScriptRoot ("v05_synthetic_results\\" + $id)
    & $runner @pyArgs -m engine.three_convex_v05.run_offline --synthetic-qa --output-dir $dest
    if ($LASTEXITCODE -ne 0) { throw "OFFLINE_QA_FAIL_CLOSED" }
    Write-Output "V05_SHADOW_QA_ONLY_PASS"
    Write-Output "NO_LIVE_GO / NO_ORDERS / NO_AUTH"
} finally {
    Pop-Location
}
