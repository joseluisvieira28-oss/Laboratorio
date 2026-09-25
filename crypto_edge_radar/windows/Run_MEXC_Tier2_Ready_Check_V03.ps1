$ErrorActionPreference = "Stop"

$radarRoot = Split-Path -Parent $PSScriptRoot
$secretDir = Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
$keyPath = Join-Path $secretDir "mexc_api_key.dpapi"
$secretPath = Join-Path $secretDir "mexc_api_secret.dpapi"

function Unprotect-LocalSecret([string]$Path) {
    $cipher = Get-Content -Raw -Path $Path
    $secure = ConvertTo-SecureString $cipher
    $credential = New-Object System.Management.Automation.PSCredential("local", $secure)
    return $credential.GetNetworkCredential().Password
}

if (-not (Test-Path $keyPath) -or -not (Test-Path $secretPath)) {
    throw "MEXC DPAPI credentials not found. Run Set_MEXC_Preflight_Secrets.ps1 first."
}

$apiKey=$null; $apiSecret=$null; $expectedEquity=$null
try {
    $apiKey=Unprotect-LocalSecret $keyPath
    $apiSecret=Unprotect-LocalSecret $secretPath
    $expectedEquity=Read-Host "MEXC Futures equity USDT shown in the app"
    if ([string]::IsNullOrWhiteSpace($expectedEquity)) { throw "Expected equity is required." }
    $env:MEXC_API_KEY=$apiKey
    $env:MEXC_API_SECRET=$apiSecret
    $env:MEXC_EXPECTED_FUTURES_EQUITY_USDT=$expectedEquity

    Push-Location $radarRoot
    try {
        $preflightExe=Join-Path $radarRoot "dist\MEXCAuthenticatedPreflight.exe"
        if (-not (Test-Path $preflightExe)) { throw "MEXCAuthenticatedPreflight.exe missing." }
        & $preflightExe
        $receipt=Join-Path $radarRoot "mexc_authenticated_preflight_receipt.json"
        if (-not (Test-Path $receipt)) { throw "Preflight receipt missing." }
        $pf=Get-Content $receipt -Raw | ConvertFrom-Json

        $riskOut=Join-Path $radarRoot "mexc_tier2_account_risk_state.json"
        $riskExe=Join-Path $radarRoot "dist\MEXCTier2RiskState.exe"
        if (-not (Test-Path $riskExe)) { throw "MEXCTier2RiskState.exe missing." }
        & $riskExe --preflight $receipt --receipt-root (Join-Path $radarRoot "live_receipts") --out $riskOut
        $risk=Get-Content $riskOut -Raw | ConvertFrom-Json

        $venueMin=[double]$pf.checks.contract.minimum_executable_notional_estimate_usdt
        $cap=10.0
        $venuePass=($venueMin -le $cap)

        Write-Host ""
        Write-Host "================ CRYPTO LAB TIER2 MICRO-LIVE READY CHECK V0.3 ================"
        Write-Host ("MEXC AUTH PREFLIGHT        : " + $(if($pf.pass){"PASS"}else{"FAIL_CLOSED"}))
        Write-Host ("ACCOUNT RISK FIREWALL     : " + $risk.status)
        Write-Host ("VENUE MIN NOTIONAL        : " + [math]::Round($venueMin,4) + " USDT")
        Write-Host ("MICRO-LIVE HARD CAP       : 10.0000 USDT")
        Write-Host ("VENUE FITS CAP            : " + $(if($venuePass){"PASS"}else{"BLOCKED"}))
        Write-Host ("DAILY REALIZED LOSS       : " + [math]::Round([double]$risk.daily_realized_loss_usdt,4) + " / 2.0000 USDT")
        Write-Host ("ROLLING 7D REALIZED LOSS  : " + [math]::Round([double]$risk.rolling_7d_realized_loss_usdt,4) + " / 5.0000 USDT")
        Write-Host ("OPEN MICRO-LIVE POSITIONS : " + [int]$risk.open_micro_live_positions)
        Write-Host "-----------------------------------------------------------------------------"
        if ($pf.pass -eq $true -and $risk.status -eq "PASS" -and $venuePass) {
            Write-Host "STATE: INFRA + CAPITAL ENVELOPE READY."
            Write-Host "NEXT: canonical OPTIONS SHORT signal + immutable active authority."
        } else {
            Write-Host "STATE: BLOCKED / NO ORDER."
        }
        Write-Host "This ready-check is READ-ONLY and never creates an order."
        Write-Host "=============================================================================="
        if ($pf.pass -ne $true -or $risk.status -ne "PASS" -or -not $venuePass) { exit 2 }
        exit 0
    } finally { Pop-Location }
} finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_EXPECTED_FUTURES_EQUITY_USDT -ErrorAction SilentlyContinue
    $apiKey=$null; $apiSecret=$null; $expectedEquity=$null
}
