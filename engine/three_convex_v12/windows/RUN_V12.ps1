# V12 only reads previously configured Telegram DPAPI; MEXC secrets untouched.
param([switch]$Once)
$ErrorActionPreference='Stop'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV12'
$exe=Join-Path $root 'V12_FinalFour_Signals.exe'
$tg=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07\secrets\telegram_bot_token.dpapi'
$chat=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07\secrets\telegram_chat_id.txt'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf) -or -not (Test-Path -LiteralPath $tg -PathType Leaf) -or -not (Test-Path -LiteralPath $chat -PathType Leaf)) {throw 'V12_MISSING_REQUIREMENTS'}
try {
    $cipher=(Get-Content -LiteralPath $tg -Raw).TrimEnd([char[]]"`r`n")
    if ($cipher -notmatch '\A(?:[a-fA-F0-9]{2})+\z') {throw 'DPAPI_PAYLOAD_INVALID'}
    $secure=ConvertTo-SecureString -String $cipher -ErrorAction Stop
    $credential=New-Object Management.Automation.PSCredential('local',$secure)
    $env:TELEGRAM_BOT_TOKEN=$credential.GetNetworkCredential().Password
    $env:TELEGRAM_CHAT_ID=(Get-Content -LiteralPath $chat -Raw).Trim()
    if ($env:TELEGRAM_CHAT_ID -notmatch '\A-?[0-9]{4,20}\z') {throw 'TELEGRAM_CHAT_ID_INVALID'}
    $args=@('--data-dir',(Join-Path $root 'data'))
    if ($Once) {$args+='--once'}
    & $exe @args
    if ($LASTEXITCODE -ne 0) {throw 'V12_OBSERVER_NONZERO_EXIT'}
} finally {
    Remove-Item Env:TELEGRAM_BOT_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:TELEGRAM_CHAT_ID -ErrorAction SilentlyContinue
}
