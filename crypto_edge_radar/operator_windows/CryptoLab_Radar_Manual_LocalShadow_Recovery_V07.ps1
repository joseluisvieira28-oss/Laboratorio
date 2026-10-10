<#
Crypto Lab V0.7 - Manual, bounded Windows PUBLIC-SHADOW recovery.
Default mode is READ ONLY (except writing a local TEMP receipt).
-StartLocalShadow explicitly starts the EXISTING local Radar .exe, not its legacy
watchdog/launcher; creates only NEW timestamped stdout/stderr log files.
No broker or authenticated account access. No MEXC credentials or trading.
Does not delete old logs, kill processes, edit Task Scheduler, touch Render,
or connect to Supabase. Never paste, upload or share raw logs/snapshots.
The reference SHA256 below is pinned to the operator's V06 local receipt,
NOT an independently verified publisher signature or original release hash.
#>
[CmdletBinding()]
param(
    [switch]$StartLocalShadow,
    [string]$ExpectedExeSha256 = "EFA25C10C9901A62173250BF147F8206D2A63722F815895AAE18FC73DA7FA5BD",
    [string]$RootDirectory = "",
    [string]$ReceiptPath = ""
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ReceiptPath)) {
    $ReceiptPath = Join-Path $env:TEMP "CryptoLab_Radar_Manual_Recovery_V07.json"
}
function Write-Receipt($Value) {
    $directory = Split-Path -Parent $ReceiptPath
    if (-not (Test-Path -LiteralPath $directory -PathType Container)) { throw "Receipt directory missing" }
    [IO.File]::WriteAllText($ReceiptPath, (($Value | ConvertTo-Json -Depth 8) + [Environment]::NewLine), (New-Object Text.UTF8Encoding($false)))
}
function NodeCount {
    return @(Get-Process -Name "CryptoEdgeRadarNode" -ErrorAction SilentlyContinue).Count
}
function ListenerCount {
    try { return @(Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue).Count } catch { return 0 }
}
function MemoryFreeGb {
    try {
        $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
        return [math]::Round(([double]$os.FreePhysicalMemory * 1KB / 1GB), 2)
    } catch { return $null }
}
function DriveFreeGb([string]$Root) {
    try {
        $drive = [IO.Path]::GetPathRoot($Root).TrimEnd([char]92)
        $disk = Get-CimInstance Win32_LogicalDisk -Filter ("DeviceID='" + $drive + "'") -ErrorAction Stop
        return [math]::Round(([double]$disk.FreeSpace / 1GB), 2)
    } catch { return $null }
}
function TaskState {
    try {
        $task = Get-ScheduledTask -TaskName "CryptoEdgeRadarV0144" -ErrorAction Stop
        return [string]$task.State
    } catch { return "UNVERIFIED" }
}
function SafeBuild([string]$Text) {
    try {
        $row = $Text | ConvertFrom-Json -ErrorAction Stop
        return (
            [string]$row.status -eq "PASS" -and
            [string]$row.build_id -eq "v0.14.4-win-cirv-eight-motor" -and
            [string]$row.registry_version -eq "3.7" -and
            [int]$row.candidate_count -eq 8 -and
            $row.cirv_strategy_present -eq $true
        )
    } catch { return $false }
}
if ([string]::IsNullOrWhiteSpace($RootDirectory)) {
    $task = Get-ScheduledTask -TaskName "CryptoEdgeRadarV0144" -ErrorAction Stop
    $action = @($task.Actions)[0]
    $m = [regex]::Match([string]$action.Arguments,'(?i)-File\s+(?:"([^"]+\.ps1)"|([^\s"]+\.ps1))')
    if (-not $m.Success) { throw "Unable to resolve approved V0144 watchdog" }
    $watchdog = if ($m.Groups[1].Success) { $m.Groups[1].Value } else { $m.Groups[2].Value }
    $watchdog = [Environment]::ExpandEnvironmentVariables($watchdog)
    if (-not [IO.Path]::IsPathRooted($watchdog)) {
        if ([string]::IsNullOrWhiteSpace([string]$action.WorkingDirectory)) { throw "Relative watcher without working directory" }
        $watchdog = Join-Path ([string]$action.WorkingDirectory) $watchdog
    }
    if ([IO.Path]::GetFileName($watchdog) -ne "RUN_RADAR_24X7_V0144.ps1") { throw "Unexpected watchdog name" }
    if (-not (Test-Path -LiteralPath $watchdog -PathType Leaf)) { throw "Watchdog missing" }
    $RootDirectory = Split-Path -Parent (Split-Path -Parent $watchdog)
}
if (-not (Test-Path -LiteralPath $RootDirectory -PathType Container)) { throw "Radar root missing" }
$RootDirectory = (Get-Item -LiteralPath $RootDirectory).FullName
$exe = Join-Path $RootDirectory "CryptoEdgeRadarNode\CryptoEdgeRadarNode.exe"
$exePresent = Test-Path -LiteralPath $exe -PathType Leaf
$hash = if ($exePresent) { (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash } else { $null }
$shaMatch = $exePresent -and $hash -eq $ExpectedExeSha256.ToUpperInvariant()
$nodes = NodeCount
$listeners = ListenerCount
$taskState = TaskState
$freeRam = MemoryFreeGb
$freeDisk = DriveFreeGb $RootDirectory
$resourcePass = $null -ne $freeRam -and $freeRam -ge 1.0 -and $null -ne $freeDisk -and $freeDisk -ge 3.0
$noCollision = $nodes -eq 0 -and $listeners -eq 0 -and $taskState -eq "Ready"

$snapshotConfirmed = $false
$backupFileCount = 0
$snapshotReceipt = Join-Path $env:TEMP "CryptoLab_Radar_Recovery_Prep_V06.json"
try {
    if (Test-Path -LiteralPath $snapshotReceipt -PathType Leaf) {
        $old = Get-Content -LiteralPath $snapshotReceipt -Raw | ConvertFrom-Json
        $recent = ([datetimeoffset]::UtcNow - [datetimeoffset]::Parse([string]$old.checked_utc)).TotalHours -le 48
        $snapshotParent = Join-Path $env:LOCALAPPDATA "CryptoLab\RadarV0144RecoverySnapshots"
        $dirs = @(Get-ChildItem -LiteralPath $snapshotParent -Directory -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTimeUtc -Descending)
        if (@($dirs).Count -gt 0) {
            $backupFileCount = @(
                Get-ChildItem -LiteralPath $dirs[0].FullName -File -Recurse -ErrorAction Stop
            ).Count
        }
        $snapshotConfirmed = (
            [string]$old.schema -eq "CRYPTO_LAB_RADAR_LOCAL_RECOVERY_PREP_V0.6" -and
            $old.snapshot_complete -eq $true -and
            [string]$old.node_exe_sha256 -eq $hash -and
            [int]$old.snapshot_file_count -ge 1 -and
            $backupFileCount -ge [int]$old.snapshot_file_count -and $recent
        )
    }
} catch { $snapshotConfirmed = $false }
$gatePass = $exePresent -and $shaMatch -and $noCollision -and $resourcePass -and $snapshotConfirmed

$report = [ordered]@{
    schema = "CRYPTO_LAB_WINDOWS_MANUAL_LOCAL_SHADOW_RECOVERY_V0.7"
    checked_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    authority = "MANUAL_PUBLIC_LOCAL_SQLITE_SHADOW_ONLY_NO_BROKER"
    mode = if ($StartLocalShadow) { "OPERATOR_EXPLICIT_LOCAL_START" } else { "READ_ONLY_PRECHECK" }
    phase = "NO_START"
    exe_exists = $exePresent
    exe_hash_sha256 = $hash
    operator_pinned_sha256_match = $shaMatch
    independently_verified_release_signature = $false
    existing_node_process_count = $nodes
    existing_port_8787_listeners = $listeners
    v0144_task_state = $taskState
    free_ram_gb = $freeRam
    free_system_disk_gb = $freeDisk
    resource_headroom_pass = $resourcePass
    snapshot_v06_receipt_and_local_files_confirmed = $snapshotConfirmed
    snapshot_local_copied_file_count = $backupFileCount
    local_start_precheck_pass = $gatePass
    packaging_selftest_pass = $false
    launched_node_pid = $null
    loopback_http_verified = $false
    build_identity_verified = $false
    live_trading_enabled = $false
    exchange_mutation_performed_by_launcher = $false
    original_log_files_modified_by_launcher = $false
    scheduled_task_mutated = $false
    render_supabase_writer_touched = $false
    one_canonical_scientific_writer_proven = $false
    next_step = "REVIEW_OR_FIX_PRECHECK"
}
if (-not $StartLocalShadow) {
    $report["phase"] = if ($gatePass) { "PRECHECK_PASS_NO_NODE_STARTED" } else { "PRECHECK_FAIL_CLOSED_NO_NODE_STARTED" }
    Write-Receipt $report
    Write-Host ("RADAR V07: " + $report["phase"]) -ForegroundColor Green
    Write-Host ("Receipt: " + $ReceiptPath)
    Write-Host "No Radar, Task Scheduler, account or database mutation performed."
    exit 0
}
if (-not $gatePass) {
    $report["phase"] = "START_REFUSED_PRECHECK_FAILED"
    Write-Receipt $report
    Write-Host "RADAR V07: FAIL CLOSED - cannot start local shadow. Inspect sanitized receipt." -ForegroundColor Yellow
    exit 3
}

# Only isolate environment for this launcher process and its child.
# V0144 local_forward.py hardcodes database_url=None and local SQLite paths.
# Refuse to inherit broker/database transport variables from this PowerShell.
$blockedVars = @("RADAR_DATABASE_URL","DATABASE_URL","MEXC_API_KEY","MEXC_SECRET_KEY",
    "MEXC_API_SECRET","MEXC_FUTURES_API_KEY","MEXC_FUTURES_SECRET",
    "BINANCE_API_KEY","BINANCE_SECRET_KEY","TELEGRAM_BOT_TOKEN")
$present = @($blockedVars | Where-Object {
    -not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($_, "Process"))
})
if ($present.Count -gt 0) {
    $report["phase"] = "START_REFUSED_INHERITED_TRANSPORT_VARIABLES"
    Write-Receipt $report
    Write-Host "RADAR V07 refused: inherited credential/DB variable names present; values NOT read or printed." -ForegroundColor Yellow
    exit 4
}

$logDir = Join-Path $RootDirectory "logs"
if (-not (Test-Path -LiteralPath $logDir -PathType Container)) { throw "Approved Radar logs directory missing" }
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$selfOut = Join-Path $env:TEMP ("CryptoLab_Radar_V07_Selftest_" + $stamp + ".out")
$selfErr = Join-Path $env:TEMP ("CryptoLab_Radar_V07_Selftest_" + $stamp + ".err")
$env:RADAR_PACKAGING_SELFTEST = "1"
try {
    $selftest = Start-Process -FilePath $exe -WorkingDirectory $RootDirectory -PassThru -Wait -RedirectStandardOutput $selfOut -RedirectStandardError $selfErr
    $selfText = Get-Content -LiteralPath $selfOut -Raw -ErrorAction SilentlyContinue
    $report["packaging_selftest_pass"] = ($selftest.ExitCode -eq 0 -and (SafeBuild $selfText))
} finally {
    Remove-Item Env:\RADAR_PACKAGING_SELFTEST -ErrorAction SilentlyContinue
}
if (-not $report["packaging_selftest_pass"]) {
    $report["phase"] = "START_REFUSED_BAD_PACKAGE_SELFTEST"
    Write-Receipt $report
    Write-Host "RADAR V07: package identity test failed; NO collector launched." -ForegroundColor Yellow
    exit 5
}
# Recheck instantaneously before starting; do not replace/stop any incumbent.
if ((NodeCount) -gt 0 -or (ListenerCount) -gt 0 -or (TaskState) -ne "Ready") {
    $report["phase"] = "START_REFUSED_CONCURRENT_NODE_OR_WATCHDOG"
    Write-Receipt $report
    Write-Host "RADAR V07: collision guard; NO new node launched." -ForegroundColor Yellow
    exit 6
}
$stdOut = Join-Path $logDir ("radar_v07_" + $stamp + "_stdout.log")
$stdErr = Join-Path $logDir ("radar_v07_" + $stamp + "_stderr.log")
if ((Test-Path -LiteralPath $stdOut) -or (Test-Path -LiteralPath $stdErr)) { throw "New log filename collision" }
$env:RADAR_PROVIDER = "mexc_futures_public"
$env:RADAR_UNIVERSE_MODE = "core5"
$env:RADAR_DB = "data\radar_evidence.sqlite3"
$env:RADAR_STATUS = "data\radar_status.json"
$env:RADAR_NOTIFICATIONS = "data\radar_notifications.jsonl"
$env:RADAR_NO_BROWSER = "1"
$proc = Start-Process -FilePath $exe -WorkingDirectory $RootDirectory -RedirectStandardOutput $stdOut -RedirectStandardError $stdErr -PassThru
$report["launched_node_pid"] = [int]$proc.Id
$report["phase"] = "STARTED_AWAITING_LOOPBACK_VERIFICATION"
$deadline = (Get-Date).AddSeconds(65)
do {
    Start-Sleep -Seconds 2
    $proc.Refresh()
    if ($proc.HasExited) {
        $report["phase"] = "NODE_EXITED_EARLY_NO_AUTORETRY"
        break
    }
    try {
        $state = Invoke-RestMethod -Uri "http://127.0.0.1:8787/api/state" -TimeoutSec 2
        if ([string]$state.build_id -eq "v0.14.4-win-cirv-eight-motor" -and
            [string]$state.registry_version -eq "3.7" -and
            [int]$state.registry.focus_expected -eq 8 -and
            [int]$state.registry.focus_loaded -eq 8) {
            $report["loopback_http_verified"] = $true
            $report["build_identity_verified"] = $true
            $report["phase"] = "LOCAL_SQLITE_PUBLIC_SHADOW_UP_NOT_CANONICAL_CUTOVER"
            break
        }
    } catch { }
} while ((Get-Date) -lt $deadline)
if ($report["phase"] -eq "STARTED_AWAITING_LOOPBACK_VERIFICATION") {
    $report["phase"] = "LOCAL_NODE_RUNNING_BUT_8787_IDENTITY_UNVERIFIED_NO_AUTORETRY"
}
Write-Receipt $report
Write-Host ("RADAR V07: " + $report["phase"]) -ForegroundColor Yellow
Write-Host ("Receipt: " + $ReceiptPath)
Write-Host "Legacy logs preserved; no Render/Supabase switchover, no broker orders."
