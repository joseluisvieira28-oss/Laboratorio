# Crypto Lab V06 — authenticated account preflight for a FUTURES LIVE executor.
# Reads existing DPAPI secrets only on this exact Windows user context.
# Never prints plaintext secrets, never submits orders, never changes MEXC.
$ErrorActionPreference = 'Stop'
$exe=Join-Path $PSScriptRoot 'MEXC_V06_Account_Preflight.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw 'V06_EXE_NOT_FOUND_DO_NOT_RUN_OLD_V05'
}
$secretDir=Join-Path $env:LOCALAPPDATA 'CryptoEdgeRadar\secrets'
function Read-V06DPAPI {
    param([string]$Filename)
    $file=Join-Path $secretDir $Filename
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        throw 'MISSING_EXISTING_DPAPI_CREDENTIAL_FILE'
    }
    $blob=(Get-Content -Raw -LiteralPath $file).TrimEnd([char[]]"`r`n")
    if ($blob -notmatch '\A(?:[0-9a-fA-F]{2})+\z') {
        throw 'BAD_DPAPI_PAYLOAD_FORMAT'
    }
    try {
        $sec=ConvertTo-SecureString -String $blob -ErrorAction Stop
        $credential=New-Object System.Management.Automation.PSCredential('local',$sec)
        return $credential.GetNetworkCredential().Password
    } catch {
        throw 'DPAPI_NOT_DECRYPTABLE_UNDER_CURRENT_WINDOWS_USER'
    }
}
try {
    $env:MEXC_API_KEY=Read-V06DPAPI 'mexc_api_key.dpapi'
    $env:MEXC_API_SECRET=Read-V06DPAPI 'mexc_api_secret.dpapi'
    & $exe --account-check
    if ($LASTEXITCODE -ne 0) {
        throw 'V06_AUTHENTICATED_ACCOUNT_PREFLIGHT_FAILED'
    }
} finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
}
