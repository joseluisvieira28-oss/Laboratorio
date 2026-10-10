<#
Crypto Lab Windows V0.6: preserve local public-shadow Radar evidence before recovery.
Does NOT start/stop any process or task, connect to exchanges, touch Postgres,
modify scientific rules, delete/rotate original files, or access MEXC accounts.
Copies approved Radar log/data evidence to local per-run snapshot folder.
May copy confidential material already in data/logs: NEVER share the snapshot.
Only the sanitized JSON receipt (no paths, raw messages, keys) may be shared.
#>
[CmdletBinding()]
param(
    [switch]$CreateSnapshot,
    [string]$RootDirectory = "",
    [string]$OutputPath = ""
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $env:TEMP "CryptoLab_Radar_Recovery_Prep_V06.json"
}

if ([string]::IsNullOrWhiteSpace($RootDirectory)) {
    $task = Get-ScheduledTask -TaskName "CryptoEdgeRadarV0144" -ErrorAction Stop
    $action = @($task.Actions)[0]
    $pattern = '(?i)-File\s+(?:"([^"]+\.ps1)"|([^\s"]+\.ps1))'
    $match = [regex]::Match([string]$action.Arguments, $pattern)
    if (-not $match.Success) { throw "Unable to locate approved V0144 watchdog script" }
    $watchdog = if ($match.Groups[1].Success) { $match.Groups[1].Value } else { $match.Groups[2].Value }
    $watchdog = [Environment]::ExpandEnvironmentVariables($watchdog)
    if (-not [IO.Path]::IsPathRooted($watchdog)) {
        if ([string]::IsNullOrWhiteSpace([string]$action.WorkingDirectory)) {
            throw "Missing task working directory"
        }
        $watchdog = Join-Path ([string]$action.WorkingDirectory) $watchdog
    }
    if ([IO.Path]::GetFileName($watchdog) -ne "RUN_RADAR_24X7_V0144.ps1") {
        throw "Task does not point at expected V0144 script"
    }
    if (-not (Test-Path -LiteralPath $watchdog -PathType Leaf)) {
        throw "Expected V0144 watchdog script is not present"
    }
    $RootDirectory = Split-Path -Parent (Split-Path -Parent $watchdog)
}
if (-not (Test-Path -LiteralPath $RootDirectory -PathType Container)) {
    throw "Radar root directory is missing"
}
$RootDirectory = (Get-Item -LiteralPath $RootDirectory).FullName
$exe = Join-Path $RootDirectory "CryptoEdgeRadarNode\CryptoEdgeRadarNode.exe"
$exePresent = Test-Path -LiteralPath $exe -PathType Leaf
$exeHash = $null
if ($exePresent) {
    $exeHash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256 -ErrorAction Stop).Hash
}
$nodeCount = @(Get-Process -Name "CryptoEdgeRadarNode" -ErrorAction SilentlyContinue).Count
$portCount = 0
try { $portCount = @(Get-NetTCPConnection -State Listen -LocalPort 8787 -ErrorAction SilentlyContinue).Count } catch {}
$busy = ($nodeCount -gt 0 -or $portCount -gt 0)
$files = @()
foreach ($name in @("radar_stdout.log","radar_stderr.log","radar_watchdog.log","radar_launcher.log")) {
    $full = Join-Path (Join-Path $RootDirectory "logs") $name
    if (Test-Path -LiteralPath $full -PathType Leaf) {
        $item = Get-Item -LiteralPath $full
        $files += [pscustomobject]@{ Source = $item.FullName; Relative = "logs\$name"; Bytes = [long]$item.Length }
    }
}
$dataRoot = Join-Path $RootDirectory "data"
if (Test-Path -LiteralPath $dataRoot -PathType Container) {
    $extensions = @(".json",".jsonl",".db",".sqlite",".sqlite3",".wal",".shm",".sqlite3-wal",".sqlite3-shm")
    foreach ($item in @(Get-ChildItem -LiteralPath $dataRoot -File -Recurse -ErrorAction Stop)) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { continue }
        if ($extensions -notcontains $item.Extension.ToLowerInvariant()) { continue }
        $within = $item.FullName.Substring($dataRoot.Length).TrimStart([char[]]@([char]92,[char]47))
        $files += [pscustomobject]@{ Source = $item.FullName; Relative = "data\" + $within; Bytes = [long]$item.Length }
    }
}
$totalBytes = [long]0
foreach ($item in $files) { $totalBytes += $item.Bytes }

$backupParent = Join-Path $env:LOCALAPPDATA "CryptoLab\RadarV0144RecoverySnapshots"
$drive = [IO.Path]::GetPathRoot($backupParent)
$driveName = $drive.TrimEnd([char]92)
$freeBytes = $null
try {
    $disk = Get-CimInstance Win32_LogicalDisk -Filter ("DeviceID='" + $driveName + "'") -ErrorAction Stop
    $freeBytes = [long]$disk.FreeSpace
} catch { }
$headroomBytes = [long](2GB)
$tooLarge = $totalBytes -gt [long](5GB)
$diskOkay = $null -ne $freeBytes -and $freeBytes -ge ($totalBytes + $headroomBytes)

$report = [ordered]@{
    schema = "CRYPTO_LAB_RADAR_LOCAL_RECOVERY_PREP_V0.6"
    checked_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    authority = "LOCAL_BACKUP_AND_READ_ONLY_DIAGNOSTICS__NO_START"
    node_exe_exists = $exePresent
    node_exe_sha256 = $exeHash
    radar_node_process_count = $nodeCount
    port_8787_listener_count = $portCount
    backup_file_count = @($files).Count
    estimated_backup_gb = [math]::Round(($totalBytes / 1GB), 3)
    free_destination_disk_gb = if ($null -eq $freeBytes) { $null } else { [math]::Round(($freeBytes / 1GB), 2) }
    needs_2gb_disk_reserve = $true
    backup_under_5gb_ceiling = (-not $tooLarge)
    disk_space_sufficient_for_snapshot = $diskOkay
    snapshot_requested = [bool]$CreateSnapshot
    snapshot_complete = $false
    snapshot_file_count = 0
    phase = "PREFLIGHT_ONLY"
    prior_logs_deleted_or_truncated = $false
    existing_data_modified = $false
    executable_launched = $false
    task_scheduler_modified = $false
    mexc_account_read_or_mutated = $false
    remote_database_accessed = $false
    external_http_requests = $false
    canonical_single_writer_reconciled = $false
    next_step = "REVIEW_RESULT_THEN_PREPARE_CONTROLLED_PUBLIC_SHADOW_START"
}
if ($CreateSnapshot) {
    if (-not $exePresent) { throw "Executable is missing, snapshot stage stopped" }
    if ($busy) { throw "A Radar process or port listener exists: snapshot stage refused" }
    if ($tooLarge) { throw "Backup set exceeds 5 GB local safety cap" }
    if (-not $diskOkay) { throw "Insufficient free disk or reserve for safe snapshot" }
    if ($files.Count -lt 1) { throw "No approved Radar evidence files found" }
    $label = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    $backup = Join-Path $backupParent $label
    if (Test-Path -LiteralPath $backup) { throw "Destination already exists" }
    $null = New-Item -ItemType Directory -Path $backup -Force
    $copied = 0
    foreach ($entry in $files) {
        $dest = Join-Path $backup $entry.Relative
        $folder = Split-Path -Parent $dest
        if (-not (Test-Path -LiteralPath $folder)) {
            $null = New-Item -ItemType Directory -Path $folder -Force
        }
        Copy-Item -LiteralPath $entry.Source -Destination $dest -ErrorAction Stop
        $actual = (Get-Item -LiteralPath $dest -ErrorAction Stop).Length
        if ($actual -ne $entry.Bytes) { throw "Backup size mismatch, snapshot incomplete" }
        $copied++
    }
    $report["snapshot_complete"] = $true
    $report["snapshot_file_count"] = $copied
    $report["phase"] = "LOCAL_SNAPSHOT_COMPLETE_NO_COLLECTOR_STARTED"
}

$parent = Split-Path -Parent $OutputPath
if ([string]::IsNullOrWhiteSpace($parent) -or -not (Test-Path -LiteralPath $parent -PathType Container)) {
    throw "JSON receipt output directory must already exist"
}
[IO.File]::WriteAllText(
    $OutputPath, (($report | ConvertTo-Json -Depth 8) + [Environment]::NewLine),
    (New-Object Text.UTF8Encoding($false))
)
Write-Host ("RADAR V06 PREPARATION: " + $report["phase"]) -ForegroundColor Green
Write-Host ("Evidence files: " + $files.Count + "; backup size: " + $report["estimated_backup_gb"] + " GB")
Write-Host ("Snapshot complete: " + $report["snapshot_complete"] + "; reserved disk safety margin: 2 GB")
Write-Host ("Receipt: " + $OutputPath)
Write-Host "Existing evidence intact. No Radar process started. DO NOT SHARE SNAPSHOT OR LOGS."
