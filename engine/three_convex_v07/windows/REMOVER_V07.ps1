# Uninstalls only V07 read-only task and executable, preserving DPAPI secrets and receipts.
$ErrorActionPreference='Stop'
$name='CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly'
$t=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if ($t) {
    Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $name -Confirm:$false
}
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07'
$exe=Join-Path $root 'V07_Telegram_MEXC_Watcher.exe'
if (Test-Path -LiteralPath $exe) {
    Remove-Item -LiteralPath $exe -Force
}
Write-Output 'V07_REMOVIDO_DA_EXECUCAO_AUTOMATICA'
Write-Output 'DPAPI_CREDENCIAIS_E_HISTORICO_PRESERVADOS_LOCALMENTE'
Write-Output 'OUTROS_OPERADORES_NAO_ALTERADOS'
