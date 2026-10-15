# Read-only evidence. No secrets, task changes, private requests or Telegram sends.
$ErrorActionPreference='Stop'
foreach ($v in @('07','11')) {
    $name=if ($v -eq '07') {'CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly'} else {'CryptoLab-Three-CONVEX-V11-Experimental-ReadOnly'}
    $root=Join-Path $env:LOCALAPPDATA "CryptoLab\ThreeConvexV$v"
    $exe=if ($v -eq '07') {'V07_Telegram_MEXC_Watcher.exe'} else {'V11_Experimental_Signals.exe'}
    $status=if ($v -eq '07') {'V07_WATCHER_STATUS.json'} else {'V11_STATUS.json'}
    $t=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    $i=if ($t) {Get-ScheduledTaskInfo -TaskName $name} else {$null}
    $path=Join-Path $root $exe
    $s=Join-Path $root "data\$status"
    [ordered]@{
        version=$v;checked_utc=[DateTime]::UtcNow.ToString('o');task_present=[bool]$t
        task_state=if ($t) {[string]$t.State} else {$null}
        last_task_result=if ($i) {$i.LastTaskResult} else {$null}
        task_last_run=if ($i) {$i.LastRunTime.ToUniversalTime().ToString('o')} else {$null}
        exe_sha256=if (Test-Path $path) {(Get-FileHash $path -Algorithm SHA256).Hash.ToLowerInvariant()} else {$null}
        process_count=@(Get-Process -Name ([IO.Path]::GetFileNameWithoutExtension($exe)) -ErrorAction SilentlyContinue).Count
        status_file_utc=if (Test-Path $s) {(Get-Item $s).LastWriteTimeUtc.ToString('o')} else {$null}
        status=if (Test-Path $s) {Get-Content $s -Raw | ConvertFrom-Json} else {$null}
    } | ConvertTo-Json -Depth 6
}
