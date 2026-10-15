# Stop ONLY V07 Telegram read-only scheduled task. Keep historical MEXC operators unchanged.
$ErrorActionPreference='Stop'
$name='CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly'
$t=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if ($null -eq $t) { Write-Output 'V07_NAO_INSTALADO'; exit 0 }
Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
Disable-ScheduledTask -TaskName $name | Out-Null
Write-Output 'V07_TELEGRAM_PARADO_DESATIVADO; OUTRAS_TAREFAS_NAO_ALTERADAS'
