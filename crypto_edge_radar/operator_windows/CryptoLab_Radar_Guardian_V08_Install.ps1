<#
Crypto Lab Windows Radar V0.8 Guardian installer - explicit one-time cutover.
DEFAULT NO -Install = local readiness audit only, sanitized TEMP receipt.
-Install explicitly:
  (1) backs up legacy V0144 ScheduledTask XML (locally),
  (2) installs NEW, separate Guardian V08 script and scheduled task,
  (3) starts V08 supervisor WITHOUT replacing healthy running Radar,
  (4) disables only LEGACY V0144 task whose destructive launcher must never run,
  (5) verifies existing Radar PID remained alive.
Does not touch MEXC Tasks, API keys, orders, Render, Supabase or science.
NO log cleanup, NO process kill. On failed cutover, fail closed.
First login after reboot required; this does not promise unattended pre-login
operation, uninterrupted electricity/internet, or zero source outages.
#>
[CmdletBinding()]
param(
    [switch]$Install,
    [string]$GuardianSource="",
    [string]$ReceiptPath=""
)
Set-StrictMode -Version Latest
$ErrorActionPreference="Stop"
$LegacyTask="CryptoEdgeRadarV0144"
$GuardianTask="CryptoEdgeRadarSafeWatchV08"
$Build="v0.14.4-win-cirv-eight-motor"
$ExpectedExeSha="EFA25C10C9901A62173250BF147F8206D2A63722F815895AAE18FC73DA7FA5BD"
if (-not $GuardianSource) { $GuardianSource=Join-Path $PSScriptRoot "CryptoLab_Radar_Guardian_V08.ps1" }
if (-not $ReceiptPath) { $ReceiptPath=Join-Path $env:TEMP "CryptoLab_Radar_Guardian_V08_Install.json" }

function Write-Receipt($Object) {
    $parent=Split-Path -Parent $ReceiptPath
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { throw "Receipt path invalid" }
    [IO.File]::WriteAllText($ReceiptPath,(($Object|ConvertTo-Json -Depth 7)+[Environment]::NewLine),(New-Object Text.UTF8Encoding($false)))
}
function Legacy {
    return Get-ScheduledTask -TaskName $LegacyTask -ErrorAction Stop
}
function Guardian {
    return Get-ScheduledTask -TaskName $GuardianTask -ErrorAction SilentlyContinue
}
function ApprovedRoot {
    $a=@((Legacy).Actions)[0]
    $m=[regex]::Match([string]$a.Arguments,'(?i)-File\s+(?:"([^"]+\.ps1)"|([^\s"]+\.ps1))')
    if (-not $m.Success) { throw "Cannot prove known legacy task action" }
    $p=if ($m.Groups[1].Success) { $m.Groups[1].Value } else { $m.Groups[2].Value }
    $p=[Environment]::ExpandEnvironmentVariables($p)
    if (-not [IO.Path]::IsPathRooted($p)) {
        if (-not $a.WorkingDirectory) { throw "Cannot resolve task working directory" }
        $p=Join-Path ([string]$a.WorkingDirectory) $p
    }
    if ([IO.Path]::GetFileName($p) -ne "RUN_RADAR_24X7_V0144.ps1" -or
        -not (Test-Path -LiteralPath $p -PathType Leaf)) { throw "Legacy script mismatch" }
    return (Split-Path -Parent (Split-Path -Parent $p))
}
function LiveState([string]$Root) {
    $exe=Join-Path $Root "CryptoEdgeRadarNode\CryptoEdgeRadarNode.exe"
    $result=[ordered]@{
        state="UNVERIFIED"
        pid=$null
        executable_hash_match=$false
        registry_8of8=$false
        forward_fresh=$false
        forward_age_seconds=$null
    }
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { return $result }
    $result.executable_hash_match=((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash -eq $ExpectedExeSha)
    $nodes=@(Get-Process -Name "CryptoEdgeRadarNode" -ErrorAction SilentlyContinue)
    $listening=@(Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue)
    if ($nodes.Count -ne 1 -or $listening.Count -ne 1) { return $result }
    $process=$nodes[0]
    $processPath=""
    try { $processPath=[string]$process.Path } catch {}
    if (-not $processPath -or
        -not [IO.Path]::GetFullPath($processPath).Equals([IO.Path]::GetFullPath($exe),[StringComparison]::OrdinalIgnoreCase) -or
        [int]$listening[0].OwningProcess -ne [int]$process.Id) { return $result }
    $result.pid=[int]$process.Id
    try {
        $api=Invoke-RestMethod -Uri "http://127.0.0.1:8787/api/state" -TimeoutSec 4 -ErrorAction Stop
        $result.registry_8of8=([string]$api.build_id -eq $Build -and
            [string]$api.registry_version -eq "3.7" -and
            [int]$api.registry.focus_loaded -eq 8 -and
            [int]$api.registry.focus_expected -eq 8)
    } catch {}
    $file=Get-Item -LiteralPath (Join-Path $Root "data\forward_local_status.json") -ErrorAction SilentlyContinue
    if ($null -ne $file) {
        $age=[math]::Round(((Get-Date).ToUniversalTime()-$file.LastWriteTimeUtc).TotalSeconds,1)
        $result.forward_age_seconds=$age
        $result.forward_fresh=($age -ge -30 -and $age -le 180)
    }
    if ($result.executable_hash_match -and $result.registry_8of8 -and $result.forward_fresh) {
        $result.state="ALIVE_HEALTHY_LOCAL_SHADOW"
    } else {
        $result.state="INCOMPLETE_FAIL_CLOSED"
    }
    return $result
}
function New-Report([string]$Phase,[bool]$CheckPass,$Before,$After) {
    return [ordered]@{
        schema="CRYPTO_LAB_WINDOWS_GUARDIAN_V08_INSTALL_V0.1"
        checked_utc=[datetimeoffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
        phase=$Phase
        default_mode=if ($Install) { "EXPLICIT_SCHEDULED_TASK_CUTOVER" } else { "READ_ONLY_PRECHECK" }
        precheck_pass=$CheckPass
        live_before=$Before
        live_after=$After
        legacy_task_enabled=if ($null -ne (Get-ScheduledTask -TaskName $LegacyTask -ErrorAction SilentlyContinue)) {
            [bool](Legacy).Settings.Enabled
        } else { $null }
        guardian_task_state=if ($null -ne (Guardian)) { [string](Guardian).State } else { "NOT_INSTALLED" }
        prior_evidence_logs_untouched=$true
        render_supabase_writer_untouched=$true
        mexc_tasks_or_orders_untouched=$true
        existing_node_never_killed=$true
        current_host_requires_login_for_autostart=$true
        canonical_single_writer_proven=$false
    }
}
$legacy=Legacy
$guard=Guardian
$root=ApprovedRoot
$exe=Join-Path $root "CryptoEdgeRadarNode\CryptoEdgeRadarNode.exe"
$backupDir=Join-Path $root "logs"
$sourceValid=(Test-Path -LiteralPath $GuardianSource -PathType Leaf)
$srcSha=$null
$dest=Join-Path $root "windows\CryptoLab_Radar_Guardian_V08.ps1"
$destExists=Test-Path -LiteralPath $dest -PathType Leaf
if ($sourceValid) { $srcSha=(Get-FileHash -LiteralPath $GuardianSource -Algorithm SHA256).Hash }
$copySlotFree=(-not $destExists) -or ($srcSha -eq (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash)
$live=LiveState $root
$ready=($legacy.Settings.Enabled -eq $true -and
    [string]$legacy.State -eq "Ready" -and
    $null -eq $guard -and
    $sourceValid -and
    $copySlotFree -and
    $live.state -eq "ALIVE_HEALTHY_LOCAL_SHADOW" -and
    (Test-Path -LiteralPath $backupDir -PathType Container))
if (-not $Install) {
    $report=New-Report "INSTALL_PRECHECK_ONLY" $ready $live $null
    Write-Receipt $report
    Write-Host ("GUARDIAN V08 INSTALL PRECHECK: "+$ready)
    Write-Host ("Receipt: "+$ReceiptPath)
    Write-Host "No Scheduler tasks or processes changed."
    exit 0
}
if (-not $ready) {
    $report=New-Report "INSTALL_REFUSED_PRECHECK_FAILED" $false $live $null
    Write-Receipt $report
    Write-Host "INSTALL REFUSED: fix healthy local Radar or old task state first."
    exit 3
}
$installPhase="INSTALL_STARTED_NOT_COMMITTED"
# Local-only backup of the precise old task; do not print or share XML, path, action.
$xml=[string](Export-ScheduledTask -TaskName $LegacyTask -ErrorAction Stop)
if ([string]::IsNullOrWhiteSpace($xml)) { throw "Cannot back up old task, installation aborted" }
$stamp=[datetimeoffset]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")
$backup=Join-Path $backupDir ("CryptoLab_Guardian_V08_legacy_task_backup_"+$stamp+".xml")
if (Test-Path -LiteralPath $backup) { throw "Task backup collision" }
[IO.File]::WriteAllText($backup,$xml,(New-Object Text.UTF8Encoding($false)))
if (-not $destExists) {
    Copy-Item -LiteralPath $GuardianSource -Destination $dest -ErrorAction Stop
}
if ((Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash -ne $srcSha) {
    throw "Installed V08 guardian script hash mismatch. Do not continue."
}
# Create and launch a separate V08 task while old task is still enabled.
# Recovery on V08 is GUARDED by old task being disabled; V08 only adopts the node now.
$action=New-ScheduledTaskAction -Execute "powershell.exe" -Argument ('-NoProfile -ExecutionPolicy Bypass -File "'+$dest+'" -Watch -EnableAutoRecover -PollSeconds 60')
$trigger=New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable -MultipleInstances IgnoreNew
$principal=New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $GuardianTask -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Crypto Lab V08 guarded public-shadow local Radar guardian; no brokerage orders" -ErrorAction Stop | Out-Null
Start-ScheduledTask -TaskName $GuardianTask -ErrorAction Stop
Start-Sleep -Seconds 5
$guardNow=Guardian
if ($null -eq $guardNow -or [string]$guardNow.State -ne "Running") {
    $report=New-Report "CUTOVER_BLOCKED_NEW_GUARDIAN_NOT_RUNNING_OLD_UNCHANGED" $true $live (LiveState $root)
    Write-Receipt $report
    Write-Host "Guardian not running: old task still untouched. Do not start any other watcher."
    exit 5
}
$stillLive=LiveState $root
if ($stillLive.state -ne "ALIVE_HEALTHY_LOCAL_SHADOW" -or $stillLive.pid -ne $live.pid) {
    $report=New-Report "CUTOVER_REFUSED_LIVE_RADAR_CHANGED_OLD_UNCHANGED" $true $live $stillLive
    Write-Receipt $report
    Write-Host "V08 monitors only; prior legacy task remains unchanged because Radar state changed."
    exit 6
}
# Disable the known unsafe task only, AFTER new guardian running and node adopted.
Disable-ScheduledTask -TaskName $LegacyTask -ErrorAction Stop | Out-Null
Start-Sleep -Seconds 2
$legacyNow=Legacy
$guardianNow=Guardian
$after=LiveState $root
$success=(-not $legacyNow.Settings.Enabled -and
    [string]$guardianNow.State -eq "Running" -and
    $after.state -eq "ALIVE_HEALTHY_LOCAL_SHADOW" -and
    $after.pid -eq $live.pid)
$report=New-Report $(if ($success) { "GUARDIAN_V08_INSTALLED_ADOPTED_NODE_OLD_TASK_DISABLED" } else { "CUTOVER_INCOMPLETE_MANUAL_REVIEW_NO_ROLLBACK" }) $true $live $after
Write-Receipt $report
Write-Host ("GUARDIAN V08: "+$report.phase)
Write-Host ("Receipt: "+$ReceiptPath)
Write-Host "Only known Radar scheduled tasks affected. No active node was restarted."
if (-not $success) { exit 7 }
