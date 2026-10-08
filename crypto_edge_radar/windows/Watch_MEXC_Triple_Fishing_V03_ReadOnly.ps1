param(
    [string]$RuntimeRoot = (Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV03"),
    [string]$TaskName = "CryptoLab-Triple-Fishing-Operator-V03",
    [int]$FreshnessSeconds = 30
)

# Strictly read-only health diagnostic. Never starts, stops, arms, disarms,
# schedules or talks to MEXC. Global slot marker != exchange position state.
$ErrorActionPreference = "Stop"
$stateFile = Join-Path $RuntimeRoot "live_state\triple_fishing_operator_v03.json"
$fatalFile = Join-Path $RuntimeRoot "live_state\TRIPLE_V03_FATAL_LAST.json"
$launchFile = Join-Path $RuntimeRoot "diagnostics\TRIPLE_V03_LAUNCH_LAST.json"
$nowUtc = [DateTimeOffset]::UtcNow
$age = $null
$heartbeatState = "MISSING"
$status = $null
$fatalPhase = $null
$launchStage = $null
$launchExit = $null

if (Test-Path -LiteralPath $stateFile -PathType Leaf) {
    try {
        $s = Get-Content -LiteralPath $stateFile -Raw | ConvertFrom-Json -ErrorAction Stop
        if ($s.version -ne "TRIPLE_FISHING_OPERATOR_V0.3") { throw "WRONG_VERSION" }
        $checked = [DateTimeOffset]::Parse([string]$s.checked_at_utc)
        if ($checked.Offset -eq [TimeSpan]::Zero -or ([string]$s.checked_at_utc) -match "(Z|[+-]\d{2}:\d{2})$") {
            $age = [math]::Round(($nowUtc - $checked.ToUniversalTime()).TotalSeconds, 2)
            $status = [string]$s.status
            $heartbeatState = if ($age -lt -2) { "CLOCK_MISMATCH" } elseif ($age -gt $FreshnessSeconds) { "STALE" } else { "FRESH" }
        } else {
            throw "TIMEZONE_REQUIRED"
        }
    } catch {
        $heartbeatState = "MALFORMED"
    }
}

# Only fixed fields from our sanitized diagnostics; no raw errors.
if (Test-Path -LiteralPath $fatalFile -PathType Leaf) {
    try {
        $f = Get-Content -LiteralPath $fatalFile -Raw | ConvertFrom-Json -ErrorAction Stop
        if ($f.schema -eq "TRIPLE_V03_FATAL_DIAGNOSTIC_V01") {
            $fatalPhase = [string]$f.phase
        }
    } catch {}
}
if (Test-Path -LiteralPath $launchFile -PathType Leaf) {
    try {
        $l = Get-Content -LiteralPath $launchFile -Raw | ConvertFrom-Json -ErrorAction Stop
        if ($l.schema -eq "TRIPLE_V03_LAUNCH_DIAGNOSTIC_V01") {
            $launchStage = [string]$l.stage
            $launchExit = $l.exit_code
        }
    } catch {}
}

$armedPresent = Test-Path -LiteralPath (Join-Path $RuntimeRoot "OPERATOR_FUTURES_V03_ARMED.json") -PathType Leaf
$killPresent = Test-Path -LiteralPath (Join-Path $RuntimeRoot "OPERATOR_FUTURES_V03_KILL_SWITCH")
$slotPresent = Test-Path -LiteralPath (Join-Path $RuntimeRoot "live_state\GLOBAL_POSITION_SLOT_V03.json") -PathType Leaf
$processPresent = [bool](Get-Process -Name "MEXCTripleFishingOperatorV03" -ErrorAction SilentlyContinue)
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
$taskState = if ($null -eq $task) { "NOT_FOUND" } else { [string]$task.State }

$health = if ($heartbeatState -ne "FRESH") {
    "UNHEALTHY_HEARTBEAT"
} elseif (-not $processPresent) {
    "NOT_RUNNING"
} elseif (-not $armedPresent -or $killPresent) {
    "MONITORING_ONLY"
} else {
    "PROCESS_AND_HEARTBEAT_PRESENT_NOT_EXCHANGE_VERIFIED"
}

$report = [ordered]@{
    schema = "TRIPLE_V03_READ_ONLY_WATCH_V01"
    observed_at_utc = $nowUtc.ToString("o")
    health = $health
    heartbeat = $heartbeatState
    heartbeat_age_seconds = $age
    supervisor_status = $status
    process_present = $processPresent
    task_state = $taskState
    armed_marker_present = $armedPresent
    kill_switch_present = $killPresent
    global_slot_file_present = $slotPresent
    fatal_phase = $fatalPhase
    launcher_last_stage = $launchStage
    launcher_last_exit_code = $launchExit
    exchange_positions_verified = $false
    trade_authority_verified = $false
    account_access_performed = $false
    exchange_mutation_performed = $false
}
$report | ConvertTo-Json -Depth 3 -Compress
