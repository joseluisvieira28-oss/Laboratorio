# Instala APENAS o monitor Telegram V07. NUNCA ativa Trading/ordens.
$ErrorActionPreference='Stop'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07'
$task='CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly'
$source=Join-Path $PSScriptRoot 'V07_Telegram_MEXC_Watcher.exe'
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw 'V07_PACKAGE_MISSING_EXE'
}
$manifest=Join-Path $PSScriptRoot 'SHA256_EXE.txt'
if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
    throw 'V07_PACKAGE_MISSING_HASH_MANIFEST'
}
$expected=([string](Get-Content -LiteralPath $manifest -Raw)).Trim().Replace('SHA256_EXE=','')
$actual=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
if ($expected -ne $actual) { throw 'V07_EXECUTABLE_SHA256_MISMATCH' }
$tg=Join-Path $root 'secrets\telegram_bot_token.dpapi'
$chat=Join-Path $root 'secrets\telegram_chat_id.txt'
if (-not (Test-Path -LiteralPath $tg) -or -not (Test-Path -LiteralPath $chat)) {
    throw 'CONFIGURAR_TELEGRAM_PRIMEIRO'
}
$mexc=Join-Path $env:LOCALAPPDATA 'CryptoEdgeRadar\secrets'
if (-not (Test-Path -LiteralPath (Join-Path $mexc 'mexc_api_key.dpapi')) -or
    -not (Test-Path -LiteralPath (Join-Path $mexc 'mexc_api_secret.dpapi'))) {
    throw 'MEXC_DPAPI_READONLY_KEYS_MISSING'
}
if (Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue) {
    throw 'V07_ALREADY_INSTALLED_CHECK_ESTADO_V07'
}
New-Item -ItemType Directory -Force -Path $root,(Join-Path $root 'data') | Out-Null
Copy-Item -LiteralPath $source -Destination (Join-Path $root 'V07_Telegram_MEXC_Watcher.exe') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'RUN_V07_TELEGRAM.ps1') -Destination (Join-Path $root 'RUN_V07_TELEGRAM.ps1') -Force
$action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -File "'+(Join-Path $root 'RUN_V07_TELEGRAM.ps1')+'"') -WorkingDirectory $root
$identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$trigger=New-ScheduledTaskTrigger -AtLogOn -User $identity
$settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $task -Trigger $trigger -Action $action -Settings $settings -Description 'Crypto Lab V07: Telegram V5 signals + authenticated MEXC read-only checks. ZERO ORDENS.' | Out-Null
Start-ScheduledTask -TaskName $task
Write-Output 'V07_TELEGRAM_READONLY_INSTALLED'
Write-Output ('TAREFA: '+$task)
Write-Output 'STATUS: PODE DEMORAR 1-3 MINUTOS NA PRIMEIRA_RECOLHA'
Write-Output 'IMPORTANTE: ZERO_ORDENS_REAIS / NENHUM_LIVE_GO'
