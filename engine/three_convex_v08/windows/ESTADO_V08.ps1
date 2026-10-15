# Local-only V08 safety receipt status; does NOT query broker or place orders.
$ErrorActionPreference='Stop'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV08'
$file=Join-Path $root 'data\V08_READINESS_STATUS.json'
if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
    Write-Output 'V08_READINESS: NENHUM_CICLO_CONCLUIDO'
    Write-Output 'EXECUCAO_REAL: DESATIVADA'
    exit 0
}
try {
    $s=Get-Content -LiteralPath $file -Raw | ConvertFrom-Json -ErrorAction Stop
    Write-Output ('UTC: '+$s.checked_at_utc)
    Write-Output ('ESTADO: '+$s.status)
    Write-Output ('MEXC_AUTH_GET_OK: '+$s.broker_authenticated_read_ok)
    Write-Output ('ACCOUNT_FLAT: '+$s.broker_account_flat_now)
    Write-Output ('HEDGE: '+$s.position_mode_hedge)
    Write-Output ('SOL_LOT_MODEL_PASS: '+$s.venue_symbols_model_pass.SOL_USDT)
    Write-Output ('BNB_LOT_MODEL_PASS: '+$s.venue_symbols_model_pass.BNB_USDT)
    Write-Output ('BLOQUEIOS_A_RESOLVER: '+$s.blockers.Count)
    foreach ($b in $s.blockers) { Write-Output ('  BLOQUEIO: '+$b) }
    Write-Output ('OLD_V07_TASK_UNCHANGED: '+$s.telegram_existing_v07_unchanged)
    Write-Output 'MEXC_MUTACOES: 0 | LIVE_GO: NAO'
} catch {
    Write-Output 'V08_STATUS_INVALIDO_FAIL_CLOSED'
    exit 2
}
