<#
Crypto Lab Radar Guardian V0.8: LOCAL-SQLITE PUBLIC-SHADOW watchdog.
DEFAULT = ONE READ-ONLY observation + sanitized TEMP receipt.
-Watch = repeated monitoring, no restart unless -EnableAutoRecover.
-Watch -EnableAutoRecover = guard-only replacement startup AFTER legacy V0144 task
has been explicitly disabled and V08 scheduled task is RUNNING.
NO existing Radar node is ever killed, replaced, or restarted.
NO previous logs are deleted, truncated, or overwritten.
NO MEXC authenticated reads/orders, no Render/Supabase Postgres writes.
Recovery is bounded: two separate missing observations, >=55 seconds apart,
one attempt in 30 minutes, max 3 attempts per UTC day, fail closed.
#>
[CmdletBinding()]
param(
    [switch]$Watch,
    [switch]$EnableAutoRecover,
    [ValidateRange(30,300)][int]$PollSeconds=60,
    [string]$RootDirectory="",
    [string]$ExpectedExeSha256="EFA25C10C9901A62173250BF147F8206D2A63722F815895AAE18FC73DA7FA5BD",
    [string]$ReceiptPath="",
    [ValidateRange(0,10)][int]$MaxIterations=0
)
Set-StrictMode -Version Latest
$ErrorActionPreference="Stop"
$Build="v0.14.4-win-cirv-eight-motor"
$LegacyTask="CryptoEdgeRadarV0144"
$GuardianTask="CryptoEdgeRadarSafeWatchV08"
if ($EnableAutoRecover -and -not $Watch) { throw "AutoRecovery requires explicit Watch mode" }
if ($EnableAutoRecover -and $RootDirectory) { throw "AutoRecovery requires approved Scheduler-derived Radar root, not override" }
if (-not $ReceiptPath) { $ReceiptPath=Join-Path $env:TEMP "CryptoLab_Radar_Guardian_V08.json" }
function Safe-WriteJson([string]$File,$Object) {
    $parent=Split-Path -Parent $File
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { throw "Receipt directory absent" }
    $temporary=$File+".tmp"
    [IO.File]::WriteAllText($temporary,(($Object|ConvertTo-Json -Depth 9)+[Environment]::NewLine),(New-Object Text.UTF8Encoding($false)))
    Move-Item -LiteralPath $temporary -Destination $File -Force
}
function Get-TaskState([string]$Name) {
    try {
        $task=Get-ScheduledTask -TaskName $Name -ErrorAction Stop
        return [pscustomobject]@{
            Exists=$true
            Enabled=[bool]$task.Settings.Enabled
            State=[string]$task.State
        }
    } catch {
        return [pscustomobject]@{ Exists=$false;Enabled=$false;State="MISSING" }
    }
}
function Get-ApprovedRoot {
    $task=Get-ScheduledTask -TaskName $LegacyTask -ErrorAction Stop
    $action=@($task.Actions)[0]
    $match=[regex]::Match([string]$action.Arguments,'(?i)-File\s+(?:"([^"]+\.ps1)"|([^\s"]+\.ps1))')
    if (-not $match.Success) { throw "Legacy Radar V0144 task has no recognized script file" }
    $watchdog=if ($match.Groups[1].Success) { $match.Groups[1].Value } else { $match.Groups[2].Value }
    $watchdog=[Environment]::ExpandEnvironmentVariables($watchdog)
    if (-not [IO.Path]::IsPathRooted($watchdog)) {
        if (-not $action.WorkingDirectory) { throw "Cannot resolve approved watchdog root" }
        $watchdog=Join-Path ([string]$action.WorkingDirectory) $watchdog
    }
    if ([IO.Path]::GetFileName($watchdog) -ne "RUN_RADAR_24X7_V0144.ps1" -or
        -not (Test-Path -LiteralPath $watchdog -PathType Leaf)) {
        throw "Legacy Radar task script identity mismatch"
    }
    return (Split-Path -Parent (Split-Path -Parent $watchdog))
}
if (-not $RootDirectory) { $RootDirectory=Get-ApprovedRoot }
if (-not (Test-Path -LiteralPath $RootDirectory -PathType Container)) { throw "Radar root is absent" }
$RootDirectory=(Get-Item -LiteralPath $RootDirectory).FullName
$Exe=Join-Path $RootDirectory "CryptoEdgeRadarNode\CryptoEdgeRadarNode.exe"
$ForwardFile=Join-Path $RootDirectory "data\forward_local_status.json"
$EvidenceDir=Join-Path $RootDirectory "data"
$LogDir=Join-Path $RootDirectory "logs"
$StateFile=Join-Path $EvidenceDir "CryptoLab_Guardian_V08_AutoRecovery_State.json"
$GuardianLog=Join-Path $LogDir "CryptoLab_Guardian_V08.jsonl"

function Get-ResourceGate {
    $freeRam=$null
    $freeDisk=$null
    try {
        $os=Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
        $freeRam=[math]::Round([double]$os.FreePhysicalMemory/1048576,2)
    } catch {}
    try {
        $drive=[IO.Path]::GetPathRoot($RootDirectory).TrimEnd([char]92)
        $disk=Get-CimInstance Win32_LogicalDisk -Filter ("DeviceID='"+$drive+"'") -ErrorAction Stop
        $freeDisk=[math]::Round([double]$disk.FreeSpace/1GB,2)
    } catch {}
    return [pscustomobject]@{
        RamFreeGb=$freeRam; DiskFreeGb=$freeDisk
        Pass=($null -ne $freeRam -and $freeRam -ge 1 -and $null -ne $freeDisk -and $freeDisk -ge 3)
    }
}
function Get-CurrentTruth {
    $nodes=@(Get-Process -Name "CryptoEdgeRadarNode" -ErrorAction SilentlyContinue)
    $listeners=@(Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue)
    $health="UNVERIFIED"
    $detail="UNVERIFIED"
    $nodePid=$null
    $forwardAge=$null
    $responseId=$false
    $safeNode=$false
    if ($nodes.Count -eq 0 -and $listeners.Count -eq 0) {
        $health="MISSING_BOTH"
        $detail="NO_RADAR_NODE_OR_8787_LISTENER"
    } elseif ($nodes.Count -ne 1 -or $listeners.Count -ne 1) {
        $health="CONFLICT_FAIL_CLOSED"
        $detail="PROCESS_OR_PORT_COUNT_MISMATCH"
    } else {
        $nodePid=[int]$nodes[0].Id
        $procPath=""
        try { $procPath=[string]$nodes[0].Path } catch {}
        $safeNode=($procPath -and
           [IO.Path]::GetFullPath($procPath).Equals([IO.Path]::GetFullPath($Exe),[StringComparison]::OrdinalIgnoreCase) -and
           [int]$listeners[0].OwningProcess -eq $nodePid)
        if (-not $safeNode) {
            $health="CONFLICT_FAIL_CLOSED"
            $detail="UNVERIFIED_PROCESS_OR_LISTENER_OWNERSHIP"
        } else {
            try {
                $state=Invoke-RestMethod -Uri "http://127.0.0.1:8787/api/state" -TimeoutSec 4 -ErrorAction Stop
                $responseId=([string]$state.build_id -eq $Build -and
                    [string]$state.registry_version -eq "3.7" -and
                    [int]$state.registry.focus_expected -eq 8 -and
                    [int]$state.registry.focus_loaded -eq 8)
            } catch {}
            $file=Get-Item -LiteralPath $ForwardFile -ErrorAction SilentlyContinue
            if ($null -ne $file) { $forwardAge=[math]::Round(((Get-Date).ToUniversalTime()-$file.LastWriteTimeUtc).TotalSeconds,1) }
            if (-not $responseId) {
                $health="ALIVE_IDENTITY_UNVERIFIED"
                $detail="NO_RESTART_WHILE_PROCESS_EXISTS"
            } elseif ($null -eq $forwardAge -or $forwardAge -lt -30 -or $forwardAge -gt 180) {
                $health="ALIVE_STALE_FORWARD_FAIL_CLOSED"
                $detail="PROCESS_IS_ALIVE_RESTART_REQUIRES_MANUAL_REVIEW"
            } else {
                $health="ALIVE_HEALTHY_LOCAL_SHADOW"
                $detail="EIGHT_MOTORS_AND_FRESH_FORWARD"
            }
        }
    }
    return [ordered]@{
        state=$health
        detail_code=$detail
        node_process_count=$nodes.Count
        port_8787_listener_count=$listeners.Count
        node_pid=$nodePid
        approved_listener_owner=$safeNode
        build_registry_8of8=$responseId
        forward_age_seconds=$forwardAge
    }
}
function Get-BackupGate {
    try {
        $receipt=Join-Path $env:TEMP "CryptoLab_Radar_Recovery_Prep_V06.json"
        if (-not (Test-Path -LiteralPath $receipt -PathType Leaf)) { return $false }
        $r=Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json -ErrorAction Stop
        if ([string]$r.schema -ne "CRYPTO_LAB_RADAR_LOCAL_RECOVERY_PREP_V0.6" -or
            $r.snapshot_complete -ne $true -or
            [int]$r.snapshot_file_count -lt 1 -or
            [string]$r.node_exe_sha256 -ne $ExpectedExeSha256) { return $false }
        $snap=Join-Path $env:LOCALAPPDATA "CryptoLab\RadarV0144RecoverySnapshots"
        $dirs=@(Get-ChildItem -LiteralPath $snap -Directory -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTimeUtc -Descending)
        if ($dirs.Count -lt 1) { return $false }
        $n=@(Get-ChildItem -LiteralPath $dirs[0].FullName -File -Recurse -ErrorAction Stop).Count
        return ($n -ge [int]$r.snapshot_file_count)
    } catch { return $false }
}
function Get-TransportGate {
    $names=@("RADAR_DATABASE_URL","DATABASE_URL","MEXC_API_KEY","MEXC_SECRET_KEY","MEXC_API_SECRET",
       "MEXC_FUTURES_API_KEY","MEXC_FUTURES_SECRET","BINANCE_API_KEY","BINANCE_SECRET_KEY",
       "TELEGRAM_BOT_TOKEN","SUPABASE_URL","SUPABASE_SERVICE_ROLE_KEY")
    foreach ($name in $names) {
        if (-not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($name,"Process"))) { return $false }
    }
    return $true
}
function Get-PackageGate {
    if (-not (Test-Path -LiteralPath $Exe -PathType Leaf)) { return $false }
    try {
        return ((Get-FileHash -LiteralPath $Exe -Algorithm SHA256 -ErrorAction Stop).Hash -eq $ExpectedExeSha256)
    } catch { return $false }
}
function Get-RecoveryState {
    if (-not (Test-Path -LiteralPath $StateFile -PathType Leaf)) {
        return [ordered]@{utc_date="";attempts_today=0;last_attempt_utc=$null}
    }
    try {
        $s=Get-Content -LiteralPath $StateFile -Raw | ConvertFrom-Json -ErrorAction Stop
        if ([int]$s.attempts_today -lt 0 -or [int]$s.attempts_today -gt 1000 -or
            [string]$s.utc_date -notmatch '^\d{4}-\d{2}-\d{2}$') { throw "State schema mismatch" }
        if ($null -ne $s.last_attempt_utc) {
            $null=[datetimeoffset]::Parse([string]$s.last_attempt_utc)
        }
        return [ordered]@{
            utc_date=[string]$s.utc_date
            attempts_today=[int]$s.attempts_today
            last_attempt_utc=$s.last_attempt_utc
        }
    } catch { throw "RECOVERY_LEDGER_INVALID_FAIL_CLOSED" }
}
function Save-RecoveryAttempt {
    $s=Get-RecoveryState
    $now=[datetimeoffset]::UtcNow
    $day=$now.ToString("yyyy-MM-dd")
    if ($s.utc_date -ne $day) { $s.utc_date=$day;$s.attempts_today=0 }
    if ($s.attempts_today -ge 3) { return "DAILY_LIMIT_EXCEEDED" }
    if ($s.last_attempt_utc) {
        $elapsed=($now-[datetimeoffset]::Parse([string]$s.last_attempt_utc)).TotalMinutes
        if ($elapsed -lt 30) { return "COOLDOWN_30MIN_ACTIVE" }
    }
    $s.attempts_today++
    $s.last_attempt_utc=$now.ToString("yyyy-MM-ddTHH:mm:ssZ")
    Safe-WriteJson $StateFile $s
    return "ATTEMPT_RECORDED"
}
function Start-GuardedLocalNode {
    # Called ONLY when watcher confirmed both process and port absent.
    $legacy=Get-TaskState $LegacyTask
    $guardian=Get-TaskState $GuardianTask
    if (-not $legacy.Exists -or $legacy.Enabled -or $legacy.State -eq "Running") { return "REFUSED_LEGACY_WATCHDOG_NOT_DISABLED" }
    if (-not $guardian.Exists -or -not $guardian.Enabled -or $guardian.State -ne "Running") { return "REFUSED_V08_SCHEDULED_GUARDIAN_NOT_RUNNING" }
    if (-not (Get-BackupGate)) { return "REFUSED_SNAPSHOT_NOT_PRESENT" }
    if (-not (Get-PackageGate)) { return "REFUSED_EXECUTABLE_HASH" }
    if (-not (Get-TransportGate)) { return "REFUSED_INHERITED_CREDENTIAL_OR_REMOTE_DB_VARIABLES" }
    if (-not (Get-ResourceGate).Pass) { return "REFUSED_LOW_RAM_OR_DISK" }
    if ((Get-CurrentTruth).state -ne "MISSING_BOTH") { return "REFUSED_CHANGED_PROCESS_OR_PORT_STATE" }
    $limit=Save-RecoveryAttempt
    if ($limit -ne "ATTEMPT_RECORDED") { return $limit }

    # Validate package identity without activating a collector.
    $mark=[datetimeoffset]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")
    $selfOut=Join-Path $env:TEMP ("CryptoLab_V08_Selftest_"+$mark+".out")
    $selfErr=Join-Path $env:TEMP ("CryptoLab_V08_Selftest_"+$mark+".err")
    $env:RADAR_PACKAGING_SELFTEST="1"
    $pass=$false
    try {
        $test=Start-Process -FilePath $Exe -WorkingDirectory $RootDirectory -PassThru -RedirectStandardOutput $selfOut -RedirectStandardError $selfErr
        if (-not $test.WaitForExit(20000)) {
            # Only our own newly spawned selftest may be stopped, never the live Radar.
            try { if (-not $test.HasExited) { $test.Kill() } } catch {}
            return "PACKAGE_SELFTEST_TIMEOUT"
        }
        $payload=Get-Content -LiteralPath $selfOut -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json -ErrorAction Stop
        $pass=($test.ExitCode -eq 0 -and
            [string]$payload.status -eq "PASS" -and
            [string]$payload.build_id -eq $Build -and
            [string]$payload.registry_version -eq "3.7" -and
            [int]$payload.candidate_count -eq 8 -and
            $payload.cirv_strategy_present -eq $true)
    } catch { return "PACKAGE_SELFTEST_FAILED" }
    finally { Remove-Item Env:\RADAR_PACKAGING_SELFTEST -ErrorAction SilentlyContinue }
    if (-not $pass) { return "PACKAGE_SELFTEST_FAILED" }

    if ((Get-CurrentTruth).state -ne "MISSING_BOTH") { return "REFUSED_CONCURRENT_NODE_AFTER_SELFTEST" }
    if (-not (Test-Path -LiteralPath $LogDir -PathType Container)) { return "REFUSED_APPROVED_LOG_DIRECTORY_MISSING" }
    $out=Join-Path $LogDir ("radar_v08_"+$mark+"_stdout.log")
    $err=Join-Path $LogDir ("radar_v08_"+$mark+"_stderr.log")
    if ((Test-Path -LiteralPath $out) -or (Test-Path -LiteralPath $err)) { return "REFUSED_NEW_LOG_COLLISION" }
    $env:RADAR_PROVIDER="mexc_futures_public"
    $env:RADAR_UNIVERSE_MODE="core5"
    $env:RADAR_DB="data\radar_evidence.sqlite3"
    $env:RADAR_STATUS="data\radar_status.json"
    $env:RADAR_NOTIFICATIONS="data\radar_notifications.jsonl"
    $env:RADAR_NO_BROWSER="1"
    try {
        $new=Start-Process -FilePath $Exe -WorkingDirectory $RootDirectory -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -ErrorAction Stop
    } catch { return "LOCAL_NODE_START_FAILED_NO_RETRY" }
    # Never force-stop even if HTTP isn't ready: leave diagnostics intact.
    $deadline=(Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 3
        if ($new.HasExited) { return "LOCAL_NODE_EXITED_EARLY_NO_RETRY" }
        $truth=Get-CurrentTruth
        if ($truth.state -eq "ALIVE_HEALTHY_LOCAL_SHADOW") { return "LOCAL_NODE_RECOVERED_AND_FRESH" }
    }
    return "LOCAL_NODE_START_UNVERIFIED_LEAVE_RUNNING_MANUAL_REVIEW"
}
function Append-GuardianLog($Record) {
    if (-not $Watch) { return }
    if (-not (Test-Path -LiteralPath $LogDir -PathType Container)) { throw "Log directory missing" }
    if (Test-Path -LiteralPath $GuardianLog -PathType Leaf) {
        if ((Get-Item -LiteralPath $GuardianLog).Length -gt 1048576) {
            $archive=Join-Path $LogDir "CryptoLab_Guardian_V08_previous.jsonl"
            if (Test-Path -LiteralPath $archive) { Remove-Item -LiteralPath $archive -Force }
            Move-Item -LiteralPath $GuardianLog -Destination $archive
        }
    }
    Add-Content -LiteralPath $GuardianLog -Value (($Record|ConvertTo-Json -Depth 6 -Compress)) -Encoding UTF8
}
$mutex=$null
$acquired=$false
if ($Watch) {
    $mutex=New-Object System.Threading.Mutex($false,"Local\CryptoEdgeRadarSafeWatchV08")
    $acquired=$mutex.WaitOne(0)
    if (-not $acquired) { throw "V08_GUARDIAN_ALREADY_RUNNING" }
}
try {
    $missingSince=$null
    $index=0
    while ($true) {
        $index++
        $truth=Get-CurrentTruth
        $recovery="NOT_REQUESTED"
        if ($truth.state -eq "MISSING_BOTH") {
            if ($null -eq $missingSince) { $missingSince=[datetimeoffset]::UtcNow }
            if ($Watch -and $EnableAutoRecover) {
                $age=([datetimeoffset]::UtcNow-$missingSince).TotalSeconds
                if ($age -ge 55) {
                    $recovery=Start-GuardedLocalNode
                } else { $recovery="AWAITING_SECOND_ABSENCE_OBSERVATION" }
            }
        } else { $missingSince=$null }
        $legacy=Get-TaskState $LegacyTask
        $guardian=Get-TaskState $GuardianTask
        $receipt=[ordered]@{
            schema="CRYPTO_LAB_RADAR_LOCAL_GUARDIAN_V0.8"
            checked_utc=[datetimeoffset]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
            authority="READ_ONLY_MONITOR_OR_BOUNDED_LOCAL_SQLITE_PUBLIC_SHADOW_RECOVERY"
            iteration=$index
            mode=if (-not $Watch) { "ONCE_READ_ONLY" } elseif ($EnableAutoRecover) { "WATCH_AUTORECOVERY_GATED" } else { "WATCH_OBSERVE_ONLY" }
            local=$truth
            legacy_watchdog_enabled=$legacy.Enabled
            legacy_watchdog_state=$legacy.State
            guardian_task_state=$guardian.State
            auto_recovery_result=$recovery
            orders_created_by_guardian=$false
            mexc_account_access=$false
            canonical_postgres_writer_modified=$false
            old_stdout_or_stderr_erased=$false
            live_process_killed_or_replaced=$false
            scientific_gates_changed=$false
            warning="HISTORIC_GAPS_REMAIN_GAPS__8_OF_8_REGISTRY_DOES_NOT_PROVE_ECONOMIC_EDGE"
        }
        Safe-WriteJson $ReceiptPath $receipt
        Append-GuardianLog $receipt
        if (-not $Watch -or ($MaxIterations -gt 0 -and $index -ge $MaxIterations)) { break }
        Start-Sleep -Seconds $PollSeconds
    }
}
finally {
    if ($null -ne $mutex) {
        if ($acquired) { $mutex.ReleaseMutex() }
        $mutex.Dispose()
    }
}
Write-Host ("RADAR GUARDIAN V0.8: "+$receipt["mode"]+" / "+$receipt["local"].state)
Write-Host ("Receipt: "+$ReceiptPath)
Write-Host "No existing Radar process was stopped, no MEXC orders, no Render/Supabase cutover."
