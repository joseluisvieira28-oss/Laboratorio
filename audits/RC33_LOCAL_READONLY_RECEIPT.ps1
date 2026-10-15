param()
# Local metadata only. No engine import, API calls, DPAPI, task changes or ARM.
$ErrorActionPreference = 'Stop'
$engineRoot = Join-Path $env:LOCALAPPDATA 'CryptoLab\ConvexRadarUnifiedRC33'
$observerRoot = Join-Path $env:LOCALAPPDATA 'CryptoLab\RC33SafetyTelegramV2'
$stateRoot = Join-Path $engineRoot 'state'
$files = @()
foreach ($relative in @('app\engine.py','app\mexc_futures.py','app\market.py','config.json','state\status.json','state\ledger.json','state\KILL_SWITCH','state\LIVE_AUTHORITY.json')) {
  $path = Join-Path $engineRoot $relative
  $exists = Test-Path -LiteralPath $path -PathType Leaf
  $row = [ordered]@{File=$relative; Exists=$exists}
  if ($exists) {
    $item = Get-Item -LiteralPath $path
    $row['ModifiedUtc'] = $item.LastWriteTimeUtc.ToString('o')
    $row['SHA256'] = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
  }
  $files += [pscustomobject]$row
}
$ledgerCounts = [ordered]@{}
$ledgerPath = Join-Path $stateRoot 'ledger.json'
if (Test-Path -LiteralPath $ledgerPath) {
  $ledger = Get-Content -LiteralPath $ledgerPath -Raw | ConvertFrom-Json
  foreach ($key in @('positions','entries','exits')) {
    $prop = $ledger.PSObject.Properties[$key]
    if ($null -eq $prop -or $null -eq $prop.Value) { $ledgerCounts[$key]='UNKNOWN' }
    elseif ($prop.Value -is [array]) { $ledgerCounts[$key]=@($prop.Value).Count }
    elseif ($prop.Value -is [pscustomobject]) { $ledgerCounts[$key]=@($prop.Value.PSObject.Properties).Count }
    else { $ledgerCounts[$key]='UNEXPECTED_TYPE' }
  }
}
$processes = @(Get-CimInstance Win32_Process | Where-Object {
  $_.ProcessId -ne $PID -and $_.CommandLine -match 'ConvexRadarUnifiedRC33|RC33SafetyTelegramV2'
} | ForEach-Object {
  # Deliberately omit complete command lines (may contain secrets).
  [pscustomobject]@{PID=$_.ProcessId; ParentPID=$_.ParentProcessId; Name=$_.Name;
    Created=$_.CreationDate; Engine=($_.CommandLine -match 'engine\.py');
    Observer=($_.CommandLine -match 'tg_watch|public_observer|RC33SafetyTelegramV2');
    ArmArgument=($_.CommandLine -match '\s(arm|prearm)(\s|$)')}
})
$tasks = @(Get-ScheduledTask | Where-Object {
  $_.TaskName -match 'Crypto|Convex|RC33|MEXC|Radar' -or
  (($_.Actions | ForEach-Object {$_.Arguments}) -join ' ') -match 'ConvexRadarUnifiedRC33|RC33SafetyTelegramV2'
} | ForEach-Object {
  $info = Get-ScheduledTaskInfo -InputObject $_
  $argsText = ($_.Actions | ForEach-Object {$_.Arguments}) -join ' '
  [pscustomobject]@{Name=$_.TaskName; State=[string]$_.State;
    LastRun=$info.LastRunTime; NextRun=$info.NextRunTime; LastResult=$info.LastTaskResult;
    MultipleInstances=[string]$_.Settings.MultipleInstances;
    ActionSHA256=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($argsText)))).Replace('-','').ToLowerInvariant();
    Engine=($argsText -match 'engine\.py|Start-RC33|Run-With-Local-DPAPI');
    Observer=($argsText -match 'tg_watch|public_observer|RC33SafetyTelegramV2');
    ArmArgument=($argsText -match '\s(arm|prearm)(\s|$)')}
})
$observerFiles = @('observer_status.json','monitor_status.json','observer_events.jsonl') | ForEach-Object {
  $p=Join-Path (Join-Path $observerRoot 'state') $_
  $item=Get-Item -LiteralPath $p -ErrorAction SilentlyContinue
  [pscustomobject]@{File=$_; Exists=($null -ne $item); ModifiedUtc=if($item){$item.LastWriteTimeUtc.ToString('o')}else{$null}}
}
[pscustomobject]@{CheckedAtUtc=[DateTime]::UtcNow.ToString('o'); Files=$files;
  LocalLedgerCounts=$ledgerCounts; Processes=$processes; ScheduledTasks=$tasks;
  ObserverFiles=$observerFiles; BrokerState='NOT_QUERIED'; StopCertification='UNVERIFIED';
  LocalHealth='NOT_CERTIFIED'; MutationPerformed=$false} | ConvertTo-Json -Depth 7
