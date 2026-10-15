# Reutiliza um bot Telegram EXISTENTE sem getUpdates/webhook mutation.
# Apenas um sendMessage ao chat confirmado pelo operador. Token DPAPI local.
param([string]$ChatId = '')
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07'
$secrets = Join-Path $root 'secrets'
New-Item -ItemType Directory -Force -Path $secrets | Out-Null
Write-Output 'MODO: REUTILIZAR_BOT_EXISTENTE / NAO_ALTERAR_OPERADOR_ANTIGO'
Write-Output 'SEM getUpdates / setWebhook / deleteWebhook / ORDENS_MEXC'

# Reutilizar IDs guardados, sem consultar ou consumir a fila de updates.
$candidates = @()
if ($ChatId) { $candidates += $ChatId }
if ($env:TELEGRAM_CHAT_ID) { $candidates += $env:TELEGRAM_CHAT_ID }
$known = @(
    (Join-Path $secrets 'telegram_chat_id.txt'),
    (Join-Path $env:LOCALAPPDATA 'CryptoEdgeRadar\secrets\telegram_chat_id.txt'),
    (Join-Path $env:LOCALAPPDATA 'CryptoEdgeRadar\secrets\telegram_chat_id'),
    (Join-Path $env:LOCALAPPDATA 'CryptoEdgeRadar\telegram_chat_id.txt')
)
foreach ($file in $known) {
    if (Test-Path -LiteralPath $file -PathType Leaf) {
        $read = (Get-Content -LiteralPath $file -Raw -ErrorAction Stop).Trim()
        if ($read -match '\A-?[0-9]{4,20}\z') { $candidates += $read }
    }
}
$candidates = @($candidates | Where-Object { $_ -match '\A-?[0-9]{4,20}\z' } | Select-Object -Unique)
if ($candidates.Count -eq 1) {
    $ChatId = [string]$candidates[0]
    Write-Output 'CHAT_ID_EXISTENTE_ENCONTRADO_LOCALMENTE: SIM'
} elseif ($candidates.Count -gt 1) {
    Write-Output 'VARIOS_CHAT_IDS_EXISTENTES: e necessario escolher o destino manualmente.'
    $ChatId = Read-Host 'Escreve o CHAT ID NUMERICO do bot antigo (nao e token)'
} else {
    Write-Output 'CHAT_ID_NAO_DESCOBERTO: consulta a configuracao do operador antigo.'
    $ChatId = Read-Host 'Escreve o CHAT ID NUMERICO existente (nao e token)'
}
$ChatId = [string]$ChatId
if ($ChatId -notmatch '\A-?[0-9]{4,20}\z') {
    throw 'CHAT_ID_INVALIDO_OU_DESCONHECIDO: localizar ID no bot/operador antigo; nunca usar getUpdates aqui'
}

# Prioridade: token DPAPI ja guardado para o V07 ou para CryptoEdgeRadar.
$secure = $null
$tokenFiles = @(
    (Join-Path $secrets 'telegram_bot_token.dpapi'),
    (Join-Path $env:LOCALAPPDATA 'CryptoEdgeRadar\secrets\telegram_bot_token.dpapi')
)
foreach ($file in $tokenFiles) {
    if (Test-Path -LiteralPath $file -PathType Leaf) {
        try {
            $cipher = (Get-Content -LiteralPath $file -Raw).TrimEnd([char[]]"`r`n")
            $candidate = ConvertTo-SecureString -String $cipher -ErrorAction Stop
            $secure = $candidate
            Write-Output 'TOKEN_DPAPI_EXISTENTE_REUTILIZADO: SIM'
            break
        } catch {
            # Pode ter sido cifrado com outra conta Windows; pedir token sem o expor.
            Write-Output 'TOKEN_DPAPI_EXISTENTE_NAO_DESENCRIPTAVEL: utilizador Windows diferente'
        }
    }
}
if ($null -eq $secure) {
    $secure = Read-Host 'TOKEN do bot existente (oculto, nao cole aqui no chat)' -AsSecureString
}
$bstr = [IntPtr]::Zero
$token = $null
$uri = $null
try {
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    if ($token -notmatch '\A[0-9]{5,15}:[A-Za-z0-9_-]{30,}\z') {
        throw 'TOKEN_BOT_INVALIDO_OU_NAO_COMPATIVEL'
    }
    # getUpdates e webhooks nao sao sequer chamados.
    $uri = 'https://api.telegram.org/bot'+$token+'/sendMessage'
    $payload = @{
        chat_id = $ChatId
        text = 'Crypto Lab V07: alertas ligados ao bot existente. Este teste NAO executa ordens MEXC.'
        disable_web_page_preview = $true
    } | ConvertTo-Json -Compress
    try {
        $response = Invoke-RestMethod -Uri $uri -Method Post -TimeoutSec 15 -ContentType 'application/json' -Body ([Text.Encoding]::UTF8.GetBytes($payload)) -ErrorAction Stop
    } catch {
        # Nunca propagar URLs/HTTP exceptions que possam incluir o token.
        throw 'TELEGRAM_SENDMESSAGE_FALHOU: confirmar Chat ID, token, permissao do bot para enviar e acesso Internet'
    }
    if ($response.ok -ne $true -or $null -eq $response.result.message_id) {
        throw 'TELEGRAM_MENSAGEM_TESTE_NAO_CONFIRMADA'
    }
    # Guardar apenas apos a resposta real do Telegram confirmar o envio.
    $cipherOut = ConvertFrom-SecureString -SecureString $secure
    [IO.File]::WriteAllText((Join-Path $secrets 'telegram_bot_token.dpapi'),$cipherOut,[Text.Encoding]::UTF8)
    [IO.File]::WriteAllText((Join-Path $secrets 'telegram_chat_id.txt'),$ChatId,[Text.Encoding]::UTF8)
    Write-Output 'BOT_ANTIGO_PRESERVADO: SIM'
    Write-Output 'MENSAGEM_TESTE_CONFIRMADA_NO_CHAT: SIM'
    Write-Output 'TOKEN_GUARDADO_DPAPI_LOCAL: SIM'
    Write-Output 'TELEGRAM_CONFIGURADO: SIM'
} finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    $token = $null
    $uri = $null
    $secure = $null
    Remove-Variable bstr,token,uri -ErrorAction SilentlyContinue
}
