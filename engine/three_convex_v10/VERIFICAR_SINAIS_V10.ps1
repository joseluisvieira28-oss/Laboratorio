# Crypto Lab CONVEX V10 - diagnose the existing V07 signal watcher.
# READ-ONLY: no credentials, no MEXC POST, no task changes, no Telegram POST.
$ErrorActionPreference = 'Stop'
$taskName = 'CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly'
$dataDir = Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07\data'
$statusPath = Join-Path $dataDir 'V07_WATCHER_STATUS.json'
$queuePath = Join-Path $dataDir 'v07_events.sqlite3'
Write-Output 'CRYPTO_LAB_CONVEX_SIGNALS_V10_DIAGNOSTIC'
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($null -eq $task) {
    Write-Output 'TASK: MISSING'
} else {
    Write-Output ('TASK: ' + $task.State)
    $ti = Get-ScheduledTaskInfo -TaskName $taskName
    Write-Output ('LAST_RUN_LOCAL: ' + $ti.LastRunTime.ToString('o'))
    Write-Output ('LAST_RUN_RESULT: ' + $ti.LastTaskResult)
}
if (-not (Test-Path -LiteralPath $statusPath -PathType Leaf)) {
    Write-Output 'STATUS: MISSING; V07 execution not established'
    exit 2
}
try {
    $s = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
    # V07 writes "yyyy-MM-dd HH:mm:ss UTC", not an ISO-8601 offset string.
    # Parse exactly as UTC; never use host-local timezone for snapshot freshness.
    $stamp = [string]$s.checked_at_utc
    $utc = [datetimeoffset]::ParseExact(
        $stamp,
        "yyyy-MM-dd HH:mm:ss 'UTC'",
        [Globalization.CultureInfo]::InvariantCulture,
        [Globalization.DateTimeStyles]::AssumeUniversal
    )
    $age = ([datetimeoffset]::UtcNow - $utc).TotalMinutes
    Write-Output ('SNAPSHOT_UTC: ' + $utc.UtcDateTime.ToString('o'))
    Write-Output ('AGE_MINUTES: ' + [math]::Round($age,1))
    Write-Output ('BINANCE_SOURCE_OK: ' + $s.v5_public_source_ok)
    Write-Output ('MEXC_READ_STATUS: ' + $s.account_snapshot_status)
    Write-Output ('TELEGRAM_PENDING: ' + $s.telegram_outbox_pending)
    Write-Output ('OUTBOX_EXISTS: ' + (Test-Path -LiteralPath $queuePath -PathType Leaf))
    Write-Output 'ORDERS_AND_MUTATIONS: DISABLED'
    if ($null -eq $task -or $task.State -ne 'Running' -or $age -lt -1 -or $age -gt 5 -or $s.v5_public_source_ok -ne $true -or [int]$s.telegram_outbox_pending -gt 0) {
        Write-Output 'SIGNAL_DELIVERY_READINESS: INVESTIGATE'
        exit 2
    }
    Write-Output 'SIGNAL_DELIVERY_READINESS: MONITOR_RUNNING_NOT_PROOF_OF_SIGNAL_DELIVERY'
    exit 0
} catch {
    Write-Output ('DIAGNOSTIC_REASON_TYPE: ' + $_.Exception.GetType().Name)
    Write-Output 'SIGNAL_DELIVERY_READINESS: INVALID_OR_STALE_RECEIPT'
    exit 2
}
