# Crypto Lab incident recovery: V07 original watcher orphan processes detached from Scheduled Task.
# Inspect (default) is strictly read-only. Repair requires explicit approval AND
# verifies Ready state, original pinned SHA, and exact paths of all V07 processes.
# This does not deploy V2, does not alter V11/V12, and never makes any API requests.
[CmdletBinding()]
param(
  [ValidateSet('Inspect','Repair')][string]$Mode='Inspect',
  [string]$Approval=''
)
$ErrorActionPreference='Stop'
$taskName='CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07'
$exe=Join-Path $root 'V07_Telegram_MEXC_Watcher.exe'
$data=Join-Path $root 'data'
$statusPath=Join-Path $data 'V07_WATCHER_STATUS.json'
$original='6c1173cdb678629552424c5074035b44f81be2af6331084fb7742f4381b7004c'
$expected=[IO.Path]::GetFullPath($exe)
function Get-V07Processes {
  # A PyInstaller one-file watcher can have parent+child with same executable name.
  return @(Get-CimInstance -ClassName Win32_Process -Filter "Name='V07_Telegram_MEXC_Watcher.exe'" -ErrorAction Stop)
}
function Get-TaskState {
  return [string](Get-ScheduledTask -TaskName $taskName -ErrorAction Stop).State
}
$state=Get-TaskState
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {throw 'V07_EXE_MISSING_NO_CHANGES'}
$hash=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
$processes=Get-V07Processes
$procOutput=@($processes | ForEach-Object {
  $p=[string]$_.ExecutablePath
  [pscustomobject]@{
    pid=[int]$_.ProcessId
    parent_pid=[int]$_.ParentProcessId
    executable_matches_installed=[string]::Equals($p,$expected,[StringComparison]::OrdinalIgnoreCase)
    exe_name=if($p){[IO.Path]::GetFileName($p)}else{'UNREADABLE'}
  }
})
$age=$null
if(Test-Path -LiteralPath $statusPath -PathType Leaf){
  $age=[math]::Round(([datetime]::UtcNow-(Get-Item -LiteralPath $statusPath).LastWriteTimeUtc).TotalMinutes,2)
}
$before=[pscustomobject]@{
  mode=$Mode; task_state=$state; installed_sha256=$hash;
  is_original_exe=($hash -eq $original);process_count=$processes.Count;
  processes=$procOutput;report_age_minutes=$age
}
if($Mode -eq 'Inspect') {
  $before | ConvertTo-Json -Depth 6
  exit 0
}
if($Approval -cne 'CONFIRMO_RECUPERACAO_V07_SEM_TRADING') {throw 'APPROVAL_REQUIRED_NO_CHANGES'}
if($hash -ne $original){throw 'ORIGINAL_EXE_HASH_MISMATCH_NO_CHANGES'}
if($state -ne 'Ready'){throw 'TASK_MUST_BE_READY_NO_CHANGES'}
if($processes.Count -ne 2){throw 'EXPECTED_TWO_ORPHANED_PYINSTALLER_PROCESSES_NO_CHANGES'}
if(@($procOutput|Where-Object{-not $_.executable_matches_installed}).Count -gt 0){
  throw 'PROCESS_EXECUTABLE_PATH_UNVERIFIED_NO_CHANGES'
}
if(-not (Test-Path -LiteralPath $data -PathType Container)){throw 'V07_DATA_MISSING_NO_CHANGES'}
$other=@(
  'CryptoLab-Three-CONVEX-V11-Experimental-ReadOnly',
  'CryptoLab-CONVEX-V12-FinalFour-ReadOnly'
)
foreach($name in $other){
  if([string](Get-ScheduledTask -TaskName $name -ErrorAction Stop).State -ne 'Running'){
    throw ('OTHER_OBSERVER_NOT_RUNNING_ABORT:'+ $name)
  }
}
$killed=$false
$backup=$null
$backupOk=$false
$startRequested=$false
try {
  # Last-moment repeat identity+ownership checks to limit race to new processes.
  $current=Get-V07Processes
  $a=@($current|ForEach-Object{[int]$_.ProcessId}|Sort-Object)
  $b=@($processes|ForEach-Object{[int]$_.ProcessId}|Sort-Object)
  if($a.Count -ne 2 -or ($a -join ',') -ne ($b -join ',') -or (Get-TaskState) -ne 'Ready'){
    throw 'V07_PROCESS_SET_OR_TASK_CHANGED_ABORT'
  }
  foreach($p in $current) {
    if(-not [string]::Equals([string]$p.ExecutablePath,$expected,[StringComparison]::OrdinalIgnoreCase)){
      throw 'V07_PROCESS_PATH_CHANGED_ABORT'
    }
  }
  foreach($p in $current) {
    $pidValue=[int]$p.ProcessId
    $still=Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if($still) {
      Stop-Process -Id $pidValue -Force -ErrorAction Stop
      $killed=$true
    }
  }
  $deadline=[datetime]::UtcNow.AddSeconds(30)
  while((Get-V07Processes).Count -gt 0) {
    if([datetime]::UtcNow -ge $deadline){throw 'V07_PROCESSES_STILL_PRESENT_NO_RESTART'}
    Start-Sleep -Seconds 1
  }
  $backup=Join-Path $env:LOCALAPPDATA ('CryptoLab\CONVEX10_BACKUPS\V07_ORPHAN_RECOVERY\'+([datetime]::UtcNow.ToString('yyyyMMddTHHmmssZ')))
  New-Item -ItemType Directory -Path $backup -Force | Out-Null
  Copy-Item -LiteralPath $exe -Destination (Join-Path $backup 'original.exe') -ErrorAction Stop
  Copy-Item -LiteralPath $data -Destination (Join-Path $backup 'data') -Recurse -Force -ErrorAction Stop
  $backupOk=$true
} catch {
  $reason=$_.Exception.Message
  # Never start an additional observer while any V07 processes remain.
  if((Get-V07Processes).Count -gt 0){
    [pscustomobject]@{result='RECOVERY_BLOCKED';reason=$reason;task_state=(Get-TaskState);
      exe_processes_remaining=(Get-V07Processes).Count;backup=$backup;sqlite_restored=$false;
      next='DO_NOT_START_TASK_OR_KILL_MORE_PROCESSES_BLINDLY'}|ConvertTo-Json -Depth 5
    throw 'RECOVERY_INCOMPLETE_PROCESSES_STILL_RUNNING'
  }
  # Previous EXE is unchanged; restart if none remain, even if backup failed.
  if((Get-TaskState) -eq 'Ready') {
    Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
    $startRequested=$true
  }
  [pscustomobject]@{result='RECOVERY_PARTIAL_TASK_RESTART_REQUESTED';reason=$reason;
    backup_created=$backupOk;backup=$backup;next='VERIFY_V07_TASK_RUNNING_AND_REPORT_FRESHNESS'}|ConvertTo-Json
  throw 'RECOVERY_PARTIAL_VERIFY_V07'
}
if((Get-V07Processes).Count -gt 0){throw 'UNEXPECTED_PROCESSES_RESTART_BLOCKED'}
if((Get-TaskState) -ne 'Ready'){throw 'SCHEDULER_STATE_CHANGED_BEFORE_START'}
Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
$startRequested=$true
$healthy=$false
$waitUntil=[datetime]::UtcNow.AddSeconds(120)
$startAt=[datetime]::UtcNow
do {
  Start-Sleep -Seconds 5
  if((Get-TaskState) -ne 'Running'){break}
  if(Test-Path -LiteralPath $statusPath){
    $item=Get-Item -LiteralPath $statusPath
    if($item.LastWriteTimeUtc -ge $startAt.AddSeconds(-2)){
      try {
        $status=Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
        if($status.status -eq 'V07_TELEGRAM_PUBLIC_SIGNALS_AND_AUTH_MEXC_READONLY' -and
           $status.v5_public_source_ok -eq $true) {
          $healthy=$true;break
        }
      }catch{}
    }
  }
} while([datetime]::UtcNow -lt $waitUntil)
[pscustomobject]@{
  result=if($healthy){'V07_ORPHAN_RECOVERED_ORIGINAL_EXE_RUNNING'}else{'V07_RESTART_NOT_PROVEN_HEALTHY'};
  task_state=(Get-TaskState);executable_sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant();
  exe_processes=(Get-V07Processes).Count;backup=$backup;data_restored=$false;
  other_observers_modified=$false;orders_created=$false;telegram_e2e_proven=$false
}|ConvertTo-Json -Depth 5
if(-not $healthy){throw 'V07_RECOVERY_HEALTH_NOT_CONFIRMED'}
