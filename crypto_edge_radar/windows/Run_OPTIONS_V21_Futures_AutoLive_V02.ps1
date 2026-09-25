$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
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
    throw "MEXC DPAPI credentials missing. Existing preflight secrets are required."
}

$apiKey = $null
$apiSecret = $null
try {
    $apiKey = Unprotect-LocalSecret $keyPath
    $apiSecret = Unprotect-LocalSecret $secretPath
    $env:MEXC_API_KEY = $apiKey
    $env:MEXC_API_SECRET = $apiSecret

    $exe = Join-Path $root "dist\OptionsV21FuturesAutoLive.exe"
    if (-not (Test-Path $exe)) { throw "OptionsV21FuturesAutoLive.exe missing: $exe" }

    New-Item -ItemType Directory -Force -Path (Join-Path $root "data") | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $root "live_receipts\options_v21_futures") | Out-Null

    Push-Location $root
    try {
        & $exe --db (Join-Path $root "data\options_v21_futures_autolive.sqlite3") --receipt-root (Join-Path $root "live_receipts\options_v21_futures") --armed (Join-Path $root "AUTO_MICROLIVE_FUTURES_ARMED.json") --kill-switch (Join-Path $root "KILL_SWITCH") --status (Join-Path $root "options_v21_futures_autolive_status.json") --interval 15
        exit $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
}
finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    $apiKey = $null
    $apiSecret = $null
}
