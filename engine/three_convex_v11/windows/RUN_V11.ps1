# V11 reuses only V07 Telegram DPAPI, never MEXC API keys.
param([switch]$Once)
$ErrorActionPreference='Stop'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV11'
$exe=Join-Path $root 'V11_Experimental_Signals.exe'
$tg=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07\secrets\telegram_bot_token.dpapi'
$chat=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07\secrets\telegram_chat_id.txt'
if (-not (Test-Path $exe) -or -not (Test-Path $tg) -or -not (Test-Path $chat)) {throw 'V11_REQUIRED_FILES_MISSING'}
try {
    $cipher=(Get-Content -LiteralPath $tg -Raw).TrimEnd([char[]]"`r`n")
    if ($cipher -notmatch '\A(?:[a-fA-F0-9]{2})+\z') {throw 'V07_DPAPI_FORMAT_INVALID'}
    $secure=ConvertTo-SecureString -String $cipher -ErrorAction Stop
    $cred=[Management.Automation.PSCredential]::new('local',$secure)
    $env:TELEGRAM_BOT_TOKEN=$cred.GetNetworkCredential().Password
    $env:TELEGRAM_CHAT_ID=(Get-Content -LiteralPath $chat -Raw).Trim()
    $args=@('--data-dir',(Join-Path $root 'data'))
    if ($Once) {$args+='--once'}
    & $exe @args
    if ($LASTEXITCODE -ne 0) {throw 'V11_WORKER_NONZERO_EXIT'}
} finally {
    Remove-Item Env:TELEGRAM_BOT_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:TELEGRAM_CHAT_ID -ErrorAction SilentlyContinue
}
