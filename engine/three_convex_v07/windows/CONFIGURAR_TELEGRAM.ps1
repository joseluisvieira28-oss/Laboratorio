# V07 bot config — local, current Windows user DPAPI; no GitHub secrets.
# First create a bot with Telegram @BotFather and send /start to that bot.
$ErrorActionPreference = 'Stop'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07'
$secrets=Join-Path $root 'secrets'
New-Item -ItemType Directory -Force -Path $secrets | Out-Null
Write-Output 'TELEGRAM: cria o bot no @BotFather, depois envia /start ao TEU bot antes de continuar.'
$secure=Read-Host 'COLA TOKEN TELEGRAM DO BOT (oculto)' -AsSecureString
$bstr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
$token=$null
try {
    $token=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
}
if ($token -notmatch '\A[0-9]{5,15}:[A-Za-z0-9_-]{30,}\z') {
    $token=$null
    throw 'INVALID_BOT_TOKEN_FORMAT_NOT_STORED'
}
$rootURL='https://api.telegram.org/bot'+$token
try {
    $me=Invoke-RestMethod -Uri ($rootURL+'/getMe') -Method Get -TimeoutSec 12
    if ($me.ok -ne $true) { throw 'BOT_INVALID' }
    $updates=Invoke-RestMethod -Uri ($rootURL+'/getUpdates?limit=100&timeout=0') -Method Get -TimeoutSec 12
    if ($updates.ok -ne $true) { throw 'UPDATE_QUERY_FAILED' }
    $chatIds=@($updates.result | Where-Object {
        $_.message -and $_.message.chat.type -eq 'private' -and
        [string]$_.message.text -match '^/start(?:\s|$)'
    } | ForEach-Object { [string]$_.message.chat.id } | Select-Object -Unique)
    if ($chatIds.Count -ne 1 -or $chatIds[0] -notmatch '\A-?[0-9]{4,20}\z') {
        throw 'UNIQUE_PRIVATE_START_CHAT_NOT_FOUND'
    }
    $chatId=[string]$chatIds[0]
    $body=@{chat_id=$chatId;
           text='Crypto Lab V07: Telegram ligado. Apenas alertas de sinais V5 e leituras MEXC. SEM ORDENS.';
           disable_web_page_preview=$true} | ConvertTo-Json -Compress
    $sent=Invoke-RestMethod -Uri ($rootURL+'/sendMessage') -Method Post -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($body)) -TimeoutSec 12
    if ($sent.ok -ne $true) { throw 'TELEGRAM_TEST_MESSAGE_NOT_ACKNOWLEDGED' }
    # Save token encrypted via Windows DPAPI tied to this same logged-in user.
    $encrypted=$secure | ConvertFrom-SecureString
    [IO.File]::WriteAllText((Join-Path $secrets 'telegram_bot_token.dpapi'),$encrypted,[Text.Encoding]::UTF8)
    [IO.File]::WriteAllText((Join-Path $secrets 'telegram_chat_id.txt'),$chatId,[Text.Encoding]::UTF8)
    Write-Output 'TELEGRAM_CONFIGURADO: SIM'
    Write-Output 'MENSAGEM_TESTE_ENVIADA: SIM'
    Write-Output 'TOKEN_GUARDADO_DPAPI_LOCAL: SIM'
} catch {
    # Do not expose exception, URL, token, or Telegram API JSON.
    throw 'TELEGRAM_SETUP_BLOQUEADO: envia /start ao bot e executa de novo (nao publiques token)'
} finally {
    $token=$null
    $rootURL=$null
    Remove-Variable bstr -ErrorAction SilentlyContinue
}
