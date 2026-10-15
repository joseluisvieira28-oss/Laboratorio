# Read-only status check for V07; never invokes MEXC or places orders.
$ErrorActionPreference='Stop'
$name='CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly'
$task=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if ($null -eq $task) {
    Write-Output 'TAREFA_V07: NAO_INSTALADA'
} else {
    Write-Output ('TAREFA_V07: '+$task.State)
    $info=Get-ScheduledTaskInfo -TaskName $name
    Write-Output ('LAST_RUN: '+$info.LastRunTime)
    Write-Output ('LAST_RUN_RESULT: '+$info.LastTaskResult)
}
$data=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07\data\V07_WATCHER_STATUS.json'
if (Test-Path -LiteralPath $data -PathType Leaf) {
    try {
        $s=Get-Content -LiteralPath $data -Raw | ConvertFrom-Json
        Write-Output ('STATUS: '+$s.status)
        Write-Output ('UTC: '+$s.checked_at_utc)
        Write-Output ('MEXC_SNAPSHOT: '+$s.account_snapshot_status)
        Write-Output ('ACCOUNT_FLAT_LAST_READ: '+$s.account_flat_in_authenticated_snapshot)
        Write-Output ('BINANCE_5M_SOURCE_OK: '+$s.v5_public_source_ok)
        Write-Output ('TELEGRAM_SENT_LAST_CYCLE: '+$s.telegram_sent_this_cycle)
        Write-Output ('TELEGRAM_PENDING: '+$s.telegram_outbox_pending)
    } catch { Write-Output 'STATUS_FILE_INVALID_FAIL_CLOSED' }
} else {
    Write-Output 'STATUS: AGUARDA_A_PRIMEIRA_RECOLHA_PUBLICA_E_MEXC'
}
Write-Output 'LIVE_ORDERS: DESATIVADAS'
