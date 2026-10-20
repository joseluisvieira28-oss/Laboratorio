# Local identity only. Never prints process command lines, task arguments, or config.
$ErrorActionPreference='Stop'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab'
$files=@('RC33SafetyTelegramV2\app\tg_watch_v2.py','RC33SafetyTelegramV2\app\observer_telegram.py','RC33SafetyTelegramV2\app\public_observer.py')
$hashes=@(foreach($rel in $files){
 $p=Join-Path $root $rel
 if(Test-Path -LiteralPath $p){[pscustomobject]@{relative_path=$rel;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash}}
})
$processes=@(Get-CimInstance Win32_Process | Where-Object {
 $_.Name -match 'V07_|V11_|V12_|python' -and ($_.ExecutablePath -match 'CryptoLab|ConvexRadar' -or $_.CommandLine -match 'tg_watch_v2|public_observer')
} | ForEach-Object {
 [pscustomobject]@{pid=$_.ProcessId;parent_pid=$_.ParentProcessId;executable=$_.ExecutablePath;rc33_bridge=[bool]($_.CommandLine -match 'tg_watch_v2')}
})
$status=@(foreach($rel in @('RC33SafetyTelegramV2\state\monitor_status.json','RC33SafetyTelegramV2\state\observer_status.json','ConvexRadarUnifiedRC33\state\status.json')){
 $p=Join-Path $root $rel
 if(Test-Path -LiteralPath $p){[pscustomobject]@{relative_path=$rel;age_minutes=[math]::Round(([datetime]::UtcNow-(Get-Item -LiteralPath $p).LastWriteTimeUtc).TotalMinutes,2)}}
})
[pscustomobject]@{checked_utc=[datetime]::UtcNow.ToString('o');read_only=$true;code_hashes=$hashes;processes=$processes;status_freshness=$status} | ConvertTo-Json -Depth 6
