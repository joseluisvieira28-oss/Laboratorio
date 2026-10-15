# V08 Futures authenticated safety/readiness audit. NO EXCHANGE POST.
# Reuses existing CryptoEdgeRadar DPAPI on this SAME Windows user.
$ErrorActionPreference='Stop'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV08'
$exe=Join-Path $root 'CryptoLab_V08_Futures_Executor_PreLive.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw 'V08_EXE_NOT_INSTALLED'
}
$old=Join-Path $env:LOCALAPPDATA 'CryptoEdgeRadar\secrets'
function Unseal-V08 {
    param([string]$filename)
    $p=Join-Path $old $filename
    if (-not (Test-Path -LiteralPath $p -PathType Leaf)) {
        throw 'MEXC_LOCAL_DPAPI_CREDENTIALS_MISSING'
    }
    $cipher=(Get-Content -LiteralPath $p -Raw).TrimEnd([char[]]"`r`n")
    if ($cipher -notmatch '\A(?:[a-fA-F0-9]{2})+\z') {
        throw 'MEXC_LOCAL_DPAPI_FILE_MALFORMED'
    }
    try {
        $ss=ConvertTo-SecureString -String $cipher -ErrorAction Stop
        $cred=New-Object Management.Automation.PSCredential('local',$ss)
        return $cred.GetNetworkCredential().Password
    } catch { throw 'MEXC_DPAPI_UNSEAL_FAILED_FOR_CURRENT_USER' }
}
try {
    $env:MEXC_API_KEY=Unseal-V08 'mexc_api_key.dpapi'
    $env:MEXC_API_SECRET=Unseal-V08 'mexc_api_secret.dpapi'
    & $exe --once --data-dir (Join-Path $root 'data')
    if ($LASTEXITCODE -ne 0) {
        throw 'V08_AUTHENTICATED_ACCOUNT_READ_FAILED_NO_TRADES'
    }
} finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
}
