# Crypto Lab V07 - Telegram + MEXC Futures READ-ONLY.
# No order calls. Uses existing MEXC DPAPI same Windows user.
param([switch]$Once)
$ErrorActionPreference = 'Stop'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07'
$exe=Join-Path $root 'V07_Telegram_MEXC_Watcher.exe'
$secretDir=Join-Path $root 'secrets'
$mexcDir=Join-Path $env:LOCALAPPDATA 'CryptoEdgeRadar\secrets'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw 'MISSING_V07_EXE_INSTALL_FIRST'
}
function Unseal-LocalDPAPI {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw 'MISSING_ENCRYPTED_LOCAL_CREDENTIAL'
    }
    $cipher=(Get-Content -LiteralPath $Path -Raw).TrimEnd([char[]]"`r`n")
    if ($cipher -notmatch '\A(?:[a-fA-F0-9]{2})+\z') {
        throw 'ENCRYPTED_DPAPI_CIPHER_MALFORMED'
    }
    try {
        $ss=ConvertTo-SecureString -String $cipher -ErrorAction Stop
        $cred=New-Object Management.Automation.PSCredential('local',$ss)
        return $cred.GetNetworkCredential().Password
    } catch {
        throw 'DPAPI_CANNOT_DECRYPT_UNDER_CURRENT_WINDOWS_USER'
    }
}
try {
    $env:MEXC_API_KEY=Unseal-LocalDPAPI (Join-Path $mexcDir 'mexc_api_key.dpapi')
    $env:MEXC_API_SECRET=Unseal-LocalDPAPI (Join-Path $mexcDir 'mexc_api_secret.dpapi')
    $env:TELEGRAM_BOT_TOKEN=Unseal-LocalDPAPI (Join-Path $secretDir 'telegram_bot_token.dpapi')
    $chatFile=Join-Path $secretDir 'telegram_chat_id.txt'
    if (-not (Test-Path -LiteralPath $chatFile -PathType Leaf)) {
        throw 'MISSING_TELEGRAM_CHAT_ID_CONFIG'
    }
    $chat=(Get-Content -LiteralPath $chatFile -Raw).Trim()
    if ($chat -notmatch '\A-?[0-9]{4,20}\z') {
        throw 'TELEGRAM_CHAT_ID_MALFORMED'
    }
    $env:TELEGRAM_CHAT_ID=$chat
    $data=Join-Path $root 'data'
    $args=@('--data-dir',$data)
    if ($Once) {$args+='--once'}
    & $exe @args
    if ($LASTEXITCODE -ne 0) { throw 'V07_READONLY_MONITOR_FAILED_CHECK_STATUS' }
} finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:TELEGRAM_BOT_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:TELEGRAM_CHAT_ID -ErrorAction SilentlyContinue
}
