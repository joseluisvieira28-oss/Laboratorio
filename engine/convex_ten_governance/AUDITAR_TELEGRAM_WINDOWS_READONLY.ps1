# AUDITORIA READ-ONLY — 10 CANAS / TELEGRAM
# Não altera tarefas, ordens, credenciais ou Telegram. Não imprime Actions nem tokens.
$ErrorActionPreference='Stop'
$wanted=@(
  @{Version='V07';Name='CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly';Root='ThreeConvexV07';Exe='V07_Telegram_MEXC_Watcher.exe';Status='V07_WATCHER_STATUS.json'},
  @{Version='V11';Name='CryptoLab-Three-CONVEX-V11-Experimental-ReadOnly';Root='ThreeConvexV11';Exe='V11_Experimental_Signals.exe';Status='V11_STATUS.json'},
  @{Version='V12';Name='CryptoLab-CONVEX-V12-FinalFour-ReadOnly';Root='ThreeConvexV12';Exe='V12_FinalFour_Signals.exe';Status='V12_STATUS.json'}
)
function Read-Utc($value) {
  if (-not $value) {return $null}
  $v=[string]$value
  try {
    if ($v.EndsWith(' UTC')) {
      $dt=[datetime]::ParseExact($v,"yyyy-MM-dd HH:mm:ss 'UTC'",[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::AssumeUniversal)
      return [datetimeoffset]::new($dt.ToUniversalTime())
    }
    return [datetimeoffset]::Parse($v,[Globalization.CultureInfo]::InvariantCulture)
  } catch {return $null}
}
$now=[datetimeoffset]::UtcNow
$observations=@()
foreach($item in $wanted) {
  $t=Get-ScheduledTask -TaskName $item.Name -ErrorAction SilentlyContinue
  $info=$null
  if ($t) {
    try {$info=Get-ScheduledTaskInfo -TaskName $item.Name -ErrorAction Stop} catch {}
  }
  $root=Join-Path $env:LOCALAPPDATA ('CryptoLab\'+$item.Root)
  $exe=Join-Path $root $item.Exe
  $statusFile=Join-Path (Join-Path $root 'data') $item.Status
  $report=$null
  $parseStatus='ABSENT'
  if (Test-Path -LiteralPath $statusFile -PathType Leaf) {
    try {
      $report=Get-Content -LiteralPath $statusFile -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
      $parseStatus='OK'
    } catch {$parseStatus='UNREADABLE'}
  }
  $stamp=if ($report) {Read-Utc $report.checked_at_utc} else {$null}
  $age=if ($stamp) {[math]::Round(($now-$stamp).TotalMinutes,2)} else {$null}
  $hash=$null
  if (Test-Path -LiteralPath $exe -PathType Leaf) {
    try {$hash=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()} catch {$hash='UNREADABLE'}
  }
  $procname=[IO.Path]::GetFileNameWithoutExtension($item.Exe)
  $pCount=@(Get-Process -Name $procname -ErrorAction SilentlyContinue).Count
  $fieldNames=if($report){@($report.PSObject.Properties.Name)}else{@()}
  $sourceOk=$null
  if($fieldNames -contains 'sources_ok') {$sourceOk=$report.sources_ok}
  if($fieldNames -contains 'v5_public_source_ok') {$sourceOk=$report.v5_public_source_ok}
  $observations += [pscustomobject][ordered]@{
    version=$item.Version
    task=$item.Name
    task_found=[bool]$t
    task_state=if($t){[string]$t.State}else{$null}
    last_task_result=if($info){$info.LastTaskResult}else{$null}
    process_count=$pCount
    report_parse=$parseStatus
    report_status=if($report){$report.status}else{$null}
    report_age_min=$age
    public_source_ok=$sourceOk
    telegram_pending=if($fieldNames -contains 'telegram_pending'){$report.telegram_pending}elseif($fieldNames -contains 'telegram_outbox_pending'){$report.telegram_outbox_pending}else{$null}
    telegram_sent_this_cycle=if($fieldNames -contains 'telegram_sent_this_cycle'){$report.telegram_sent_this_cycle}else{$null}
    orders_enabled=if($fieldNames -contains 'orders_enabled'){$report.orders_enabled}elseif($fieldNames -contains 'real_order_submission_enabled'){$report.real_order_submission_enabled}else{$null}
    exe_sha256=$hash
    matches_audit_v2_preview=if($item.Version -eq 'V07' -and $hash){$hash -eq '99d06384268d649b2224a10fa9d231ad8ce78fb6ced8aaee4389f12d86e12e84'}elseif($item.Version -eq 'V11' -and $hash){$hash -eq '8143e21de4cefb59c896fbb706d59def525ff9d459cdb36e182bf0bdd33db3bc'}else{$null}
  }
}
# Lista apenas nomes, estados e classe de tarefa — NUNCA ações/argumentos.
$exact=@($wanted|ForEach-Object{$_.Name})
$all=@(Get-ScheduledTask | Where-Object {
  $_.TaskName -match '(?i)cryptolab|cryptoedge|convex|mexc|options|fishing|donchian|ced1d|radar|telegram|bnb'
})
$other=@()
foreach($t in $all) {
  if($exact -contains $t.TaskName){continue}
  $category=if ($t.TaskName -eq 'CryptoLab-OPTIONS-V21-Telegram-Watcher') {
    'LEGACY_TELEGRAM_CANDIDATE'
  }elseif($t.TaskName -match '(?i)AutoLive|Executor|Operator|Trading|Futures') {
    'MAY_MANAGE_POSITIONS_DO_NOT_DISABLE_BLINDLY'
  }else{
    'UNCLASSIFIED_REVIEW_BEFORE_DISABLE'
  }
  $other += [pscustomobject][ordered]@{
    name=$t.TaskName
    state=[string]$t.State
    category=$category
  }
}
[pscustomobject][ordered]@{
  report='CRYPTO_LAB_TEN_CANAS_TELEGRAM_INVENTORY_READONLY'
  checked_utc=$now.ToString('o')
  expected_lanes=10
  installed_observers=$observations
  other_matching_tasks=@($other|Sort-Object name)
  gitHub_main_radar_keepalive_not_inspected_locally=$true
  note='NO_TASKS_CHANGED_NO_TELEGRAM_SENT_NO_PRIVATE_API_NO_SECRETS'
} | ConvertTo-Json -Depth 8
