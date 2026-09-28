$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$secretDir = Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
$keyPath = Join-Path $secretDir "mexc_api_key.dpapi"
$secretPath = Join-Path $secretDir "mexc_api_secret.dpapi"
$outPath = Join-Path $root "operator_futures_bnb_ced1d_readiness.json"

function Unprotect-LocalSecret([string]$Path) {
    $cipher = Get-Content -Raw -Path $Path
    $secure = ConvertTo-SecureString $cipher
    $credential = New-Object System.Management.Automation.PSCredential("local", $secure)
    return $credential.GetNetworkCredential().Password
}

if (-not (Test-Path $keyPath) -or -not (Test-Path $secretPath)) {
    throw "MEXC DPAPI credentials missing. Use the existing local secret setup; never paste secrets into chat/GitHub/Drive."
}

$apiKey = $null
$apiSecret = $null
try {
    $apiKey = Unprotect-LocalSecret $keyPath
    $apiSecret = Unprotect-LocalSecret $secretPath
    $env:MEXC_API_KEY = $apiKey
    $env:MEXC_API_SECRET = $apiSecret

    $exe = Join-Path $root "dist\MEXCOperatorFuturesReadiness.exe"
    if (-not (Test-Path $exe)) {
        throw "MEXCOperatorFuturesReadiness.exe missing: $exe"
    }

    Write-Host "=== BNB + CED1D MEXC FUTURES READ-ONLY READINESS ==="
    Write-Host "No orders. No exchange mutation. Existing global Futures position => FAIL_CLOSED."
    & $exe --output $outPath
    $code = $LASTEXITCODE

    Write-Host ""
    Write-Host "=== SANITIZED RECEIPT ==="
    if (Test-Path $outPath) {
        Get-Content $outPath -Raw
    }
    exit $code
}
finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    $apiKey = $null
    $apiSecret = $null
}
