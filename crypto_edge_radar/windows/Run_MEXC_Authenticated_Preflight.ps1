$ErrorActionPreference = "Stop"

$radarRoot = Split-Path -Parent $PSScriptRoot
$secretDir = Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
$keyPath = Join-Path $secretDir "mexc_api_key.dpapi"
$secretPath = Join-Path $secretDir "mexc_api_secret.dpapi"

if (-not (Test-Path $keyPath) -or -not (Test-Path $secretPath)) {
    throw "MEXC DPAPI credentials not found. Run Set_MEXC_Preflight_Secrets.ps1 first."
}

function Unprotect-LocalSecret([string]$Path) {
    $cipher = Get-Content -Raw -Path $Path
    $secure = ConvertTo-SecureString $cipher
    $credential = New-Object System.Management.Automation.PSCredential("local", $secure)
    return $credential.GetNetworkCredential().Password
}

$apiKey = $null
$apiSecret = $null

try {
    $apiKey = Unprotect-LocalSecret $keyPath
    $apiSecret = Unprotect-LocalSecret $secretPath
    if ([string]::IsNullOrWhiteSpace($apiKey) -or [string]::IsNullOrWhiteSpace($apiSecret)) {
        throw "Decrypted API credential is empty."
    }

    $env:MEXC_API_KEY = $apiKey
    $env:MEXC_API_SECRET = $apiSecret

    Push-Location $radarRoot
    try {
        $exe = Join-Path $radarRoot "dist\MEXCAuthenticatedPreflight.exe"
        if (Test-Path $exe) {
            & $exe
            $exitCode = $LASTEXITCODE
        } elseif (Get-Command python -ErrorAction SilentlyContinue) {
            & python ".\scripts\mexc_authenticated_preflight.py"
            $exitCode = $LASTEXITCODE
        } elseif (Get-Command py -ErrorAction SilentlyContinue) {
            & py -3 ".\scripts\mexc_authenticated_preflight.py"
            $exitCode = $LASTEXITCODE
        } else {
            throw "Neither MEXCAuthenticatedPreflight.exe nor Python is available."
        }

        $receipt = Join-Path $radarRoot "mexc_authenticated_preflight_receipt.json"
        if (Test-Path $receipt) {
            Write-Host ""
            Write-Host "Sanitized receipt: $receipt"
        }
        exit $exitCode
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
