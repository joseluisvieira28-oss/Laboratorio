<#
Crypto Lab Windows Radar log forensic V0.5.
Strict READ-ONLY to Windows tasks, logs, DB, exchange, processes and network.
Only writes a sanitized JSON receipt to the operator's TEMP directory.
Does not print raw logs, exception messages, file paths or credentials.
The last 25 stdout lines may contain repetitive FAIL_CLOSED/error field names;
counting such words is NOT counting failures.
#>
[CmdletBinding()]
param(
    [string]$RootDirectory = "",
    [string]$OutputPath = ""
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Field($Object, [string]$Name) {
    if ($null -eq $Object) { return $null }
    $prop = $Object.PSObject.Properties[$Name]
    if ($null -eq $prop) { return $null }
    return $prop.Value
}
function Label($Value) {
    if ($null -eq $Value) { return "UNVERIFIED" }
    $s = [string]$Value
    if ($s -match "^[A-Za-z][A-Za-z0-9_.-]{0,79}$") { return $s }
    return "VALUE_HIDDEN"
}
function UtcStamp($Value) {
    if ($null -eq $Value) { return $null }
    $s = [string]$Value
    if ($s -match "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d\d:\d\d)$") {
        return $s
    }
    return $null
}
function FromJson([string]$Raw) {
    try { return (ConvertFrom-Json -InputObject $Raw -ErrorAction Stop) }
    catch { return $null }
}
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $env:TEMP "CryptoLab_Radar_Stdout_Forensic_V05.json"
}
if ([string]::IsNullOrWhiteSpace($RootDirectory)) {
    $task = Get-ScheduledTask -TaskName "CryptoEdgeRadarV0144" -ErrorAction Stop
    $action = @($task.Actions)[0]
    $rx = '(?i)-File\s+(?:"([^"]+\.ps1)"|([^\s"]+\.ps1))'
    $m = [regex]::Match([string]$action.Arguments, $rx)
    if (-not $m.Success) { throw "Approved watchdog script cannot be resolved" }
    $watchdog = if ($m.Groups[1].Success) { $m.Groups[1].Value } else { $m.Groups[2].Value }
    $watchdog = [Environment]::ExpandEnvironmentVariables($watchdog)
    if (-not [System.IO.Path]::IsPathRooted($watchdog)) {
        if ([string]::IsNullOrWhiteSpace([string]$action.WorkingDirectory)) {
            throw "Cannot resolve relative watchdog path; no scan performed"
        }
        $watchdog = Join-Path ([string]$action.WorkingDirectory) $watchdog
    }
    if ([System.IO.Path]::GetFileName($watchdog) -ne "RUN_RADAR_24X7_V0144.ps1") {
        throw "Unexpected watchdog filename; fail closed"
    }
    $RootDirectory = Split-Path -Parent (Split-Path -Parent $watchdog)
}
if (-not (Test-Path -LiteralPath $RootDirectory -PathType Container)) {
    throw "Approved Radar root does not exist"
}

$log = Join-Path $RootDirectory "logs\radar_stdout.log"
$logMeta = [ordered]@{
    exists = $false
    size_mb = $null
    last_write_utc = $null
    tail_lines_examined = 0
    parsed_json_lines = 0
    non_json_lines = 0
}
$sample = @()
if (Test-Path -LiteralPath $log -PathType Leaf) {
    $file = Get-Item -LiteralPath $log
    $logMeta["exists"] = $true
    $logMeta["size_mb"] = [math]::Round(([double]$file.Length / 1MB), 2)
    $logMeta["last_write_utc"] = $file.LastWriteTimeUtc.ToString("yyyy-MM-ddTHH:mm:ssZ")
    $lines = @(Get-Content -LiteralPath $log -Tail 25 -ErrorAction Stop)
    $logMeta["tail_lines_examined"] = $lines.Count
    foreach ($line in $lines) {
        $obj = FromJson ([string]$line)
        if ($null -eq $obj) {
            $logMeta["non_json_lines"]++
            continue
        }
        $logMeta["parsed_json_lines"]++
        $errorsValue = Field $obj "errors"
        $errorValue = Field $obj "error"
        $errorsCount = 0
        if ($null -ne $errorsValue) {
            if ($errorsValue -is [pscustomobject]) {
                $errorsCount = @($errorsValue.PSObject.Properties).Count
            } elseif ($errorsValue -is [array]) {
                $errorsCount = $errorsValue.Count
            } elseif ($errorsValue -is [string] -and $errorsValue.Length -gt 0) {
                $errorsCount = 1
            }
        }
        $status = Field $obj "status"
        $health = Field $obj "health"
        $component = Field $obj "component"
        $reason = Field $obj "reason"
        $sample += [ordered]@{
            event_utc = UtcStamp (Field $obj "checked_at_utc")
            status = Label $status
            health = Label $health
            component = Label $component
            reason_code = Label $reason
            error_fields_count = $errorsCount
            direct_error_present = ($null -ne $errorValue -and [string]$errorValue -ne "")
            safety_orders_created = if ($null -eq (Field $obj "orders_created")) { "UNKNOWN" } else { [bool](Field $obj "orders_created") }
        }
    }
}
$files = @()
foreach ($name in @(
    "radar_status.json",
    "forward_local_supervisor_status.json",
    "forward_local_status.json",
    "dh03_local_status.json",
    "cirv_local_status.json",
    "render_sentinel_supervisor_status.json"
)) {
    $path = Join-Path (Join-Path $RootDirectory "data") $name
    $entry = [ordered]@{
        file = $name
        exists = $false
        last_write_utc = $null
        status = "UNVERIFIED"
        health = "UNVERIFIED"
        phase = "UNVERIFIED"
        build_id = "UNVERIFIED"
        json_parsed = $false
    }
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        $info = Get-Item -LiteralPath $path
        $entry["exists"] = $true
        $entry["last_write_utc"] = $info.LastWriteTimeUtc.ToString("yyyy-MM-ddTHH:mm:ssZ")
        if ($info.Length -le 2097152) {
            $obj = FromJson ([string](Get-Content -LiteralPath $path -Raw -ErrorAction Stop))
            if ($null -ne $obj) {
                $entry["json_parsed"] = $true
                $entry["status"] = Label (Field $obj "status")
                $entry["health"] = Label (Field $obj "health")
                $entry["phase"] = Label (Field $obj "runtime_phase")
                $entry["build_id"] = Label (Field $obj "build_id")
            }
        }
    }
    $files += $entry
}
$out = [ordered]@{
    schema = "CRYPTO_LAB_LOCAL_RADAR_LOG_FORENSIC_V0.5"
    checked_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    authority = "READ_ONLY_LOGS_AND_TASK_METADATA_NO_EXECUTION"
    stdout_summary = $logMeta
    stdout_last_json_states = @($sample | Select-Object -Last 8)
    local_status_files = $files
    findings = @(
        "STRING_MATCH_COUNTS_ARE_NOT_FAILURE_COUNTS",
        "LAST_LOG_LINE_IS_NOT_PROOF_OF_CRASH_CAUSE",
        "STATE_FILE_TIMESTAMPS_ARE_NOT_PROOF_OF_CONTINUOUS_COLLECTION",
        "NO_RADAR_RESTART_OR_SECOND_WRITER_ACTIVATED"
    )
    raw_log_lines_disclosed = $false
    raw_exception_messages_disclosed = $false
    passwords_or_urls_disclosed = $false
    raw_task_actions_disclosed = $false
    trading_account_access = $false
    task_or_process_mutation = $false
    database_access = $false
    external_requests = $false
    next_step = "REVIEW_LAST_STRUCTURED_STATES_AND_STALE_LOCAL_STATUS_BEFORE_RESTART"
}
$parent = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
    throw "Receipt directory must exist"
}
[System.IO.File]::WriteAllText(
    $OutputPath, (($out | ConvertTo-Json -Depth 9) + [Environment]::NewLine),
    (New-Object System.Text.UTF8Encoding($false))
)
Write-Host ("CRYPTO LAB V0.5 READ-ONLY FORENSIC RECEIPT: " + $OutputPath)
Write-Host ("Last stdout write UTC: " + $logMeta["last_write_utc"])
Write-Host ("Last 25 lines: parsed JSON " + $logMeta["parsed_json_lines"] +
    ", non-JSON " + $logMeta["non_json_lines"])
Write-Host "No collector, Task Scheduler action, trading executor or database writer activated."
