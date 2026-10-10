<#
Crypto Lab — Windows local worker collision preflight V0.3, read-only.
PURPOSE: enumerate only six already operator-confirmed Task Scheduler names,
their timing/status, and local TCP :8787 LISTEN owner process name/PID.
DOES NOT READ: Actions.Execute, Actions.Arguments, command lines, environment
values, token/key files, account/position state, DPAPI, DB connections.
DOES NOT: launch, stop, disable, enable tasks; modify system power/network;
send traffic to any endpoint; change exchange/database/capital/evidence.
Output only one user-selected local JSON receipt (no remote data transfer).
#>
[CmdletBinding()]
param([string]$OutputPath = "")

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$approvedNames = @(
    "CryptoLab-OPTIONS-V21-Futures-AutoLive",
    "CryptoLab-OPTIONS-V21-Telegram-Watcher",
    "CryptoLab-Triple-Fishing-Operator-V03",
    "CryptoEdgeRadarTruthCockpitV0145",
    "CryptoEdgeRadarV0144",
    "CryptoLab-BNB-Operator-AutoLive-V01"
)

function TimeOrNull($value) {
    try {
        if ($null -eq $value -or $value.Year -lt 2020) { return $null }
        return $value.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    } catch { return $null }
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $env:TEMP "CryptoLab_PC_Worker_Reconciliation_V03.json"
}
$taskRows = @()
foreach ($name in $approvedNames) {
    $row = [ordered]@{
        task_name = $name
        state = "UNVERIFIED"
        enabled = $null
        last_run_utc = $null
        next_run_utc = $null
        last_result_code = $null
        multiple_instances_policy = "UNVERIFIED"
        metadata_readable = $false
        category = if ($name -match "AutoLive|Triple-Fishing|Telegram-Watcher") {
            "POTENTIAL_LIVE_EXECUTOR_OR_OPERATOR__LEAVE_UNTOUCHED"
        } else { "RADAR_TASK__NO_WRITER_INFERENCE" }
    }
    try {
        $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue |
            Where-Object { $_.TaskName -eq $name } | Select-Object -First 1
        if ($null -ne $task) {
            $row["state"] = [string]$task.State
            $row["enabled"] = [bool]$task.Settings.Enabled
            $row["multiple_instances_policy"] = [string]$task.Settings.MultipleInstances
            try {
                $info = Get-ScheduledTaskInfo -InputObject $task -ErrorAction Stop
                $row["last_run_utc"] = TimeOrNull $info.LastRunTime
                $row["next_run_utc"] = TimeOrNull $info.NextRunTime
                $row["last_result_code"] = [string]$info.LastTaskResult
                $row["metadata_readable"] = $true
            } catch {
                $row["state"] += "_TASK_INFO_UNVERIFIED"
            }
        } else { $row["state"] = "NOT_FOUND" }
    } catch { $row["state"] = "TASK_QUERY_UNAVAILABLE" }
    $taskRows += $row
}

$listening = @()
try {
    if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
        $connections = @(Get-NetTCPConnection -LocalPort 8787 -ErrorAction SilentlyContinue |
            Where-Object { $_.State -eq "Listen" })
        foreach ($connection in $connections) {
            $pidValue = [int]$connection.OwningProcess
            $nameValue = "UNVERIFIED"
            try {
                $p = Get-Process -Id $pidValue -ErrorAction Stop
                $nameValue = [string]$p.ProcessName
            } catch { }
            $listening += [ordered]@{
                port = 8787
                pid = $pidValue
                process_name = $nameValue
                local_bind_category = if ($connection.LocalAddress -in @("127.0.0.1", "::1")) {
                    "LOOPBACK_ONLY"
                } else { "BIND_ADDRESS_NOT_LOOPBACK_ONLY" }
            }
        }
    }
} catch { }
$processCounts = [ordered]@{}
foreach ($name in @("CryptoEdgeRadarNode", "python", "pythonw", "powershell", "pwsh")) {
    try {
        $processCounts[$name] = @(Get-Process -Name $name -ErrorAction SilentlyContinue).Count
    } catch { $processCounts[$name] = $null }
}
$notes = @()
if (@($taskRows | Where-Object { $_.state -eq "Running" }).Count -gt 0) {
    $notes += "ONE_OR_MORE_PREEXISTING_CRYPTO_TASKS_RUNNING_NO_CHANGES_ALLOWED"
}
if (@($listening).Count -gt 1) { $notes += "PORT_8787_MULTIPLE_LISTENERS_REVIEW" }
if (@($listening | Where-Object { $_.local_bind_category -ne "LOOPBACK_ONLY" }).Count -gt 0) {
    $notes += "PORT_8787_NONLOOPBACK_BIND_REQUIRES_PRIVACY_REVIEW"
}
if (@($taskRows | Where-Object { $_.multiple_instances_policy -eq "Parallel" }).Count -gt 0) {
    $notes += "SCHEDULED_TASK_PARALLEL_INSTANCES_CONFIGURED_REQUIRES_REVIEW"
}
$report = [ordered]@{
    schema = "CRYPTO_LAB_PC_WORKER_RECONCILIATION_V0.3"
    checked_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    authority = "LOCAL_READ_ONLY__NO_EXECUTION_OR_DB_WRITER_ACTIVATION"
    scheduled_tasks = $taskRows
    listener_8787 = $listening
    process_name_counts = $processCounts
    warnings = $notes
    unique_scientific_writer_proven = $false
    existing_mexc_positions_or_exits_inspected = $false
    task_actions_arguments_or_credentials_inspected = $false
    database_connection_or_secret_accessed = $false
    network_requests_made = $false
    any_task_or_process_started_stopped_or_modified = $false
    any_settings_changed = $false
    exchange_mutation_performed = $false
    live_trading_authorized = $false
    next_step = "REVIEW_EXISTING_TASKS_AND_RESOURCES__NO_PARALLEL_COLLECTOR"
}
$directory = Split-Path -Parent $OutputPath
if ([string]::IsNullOrWhiteSpace($directory) -or
    -not (Test-Path -LiteralPath $directory -PathType Container)) {
    throw "Output directory must exist"
}
$json = $report | ConvertTo-Json -Depth 12
[System.IO.File]::WriteAllText(
    $OutputPath, ($json+[Environment]::NewLine),
    (New-Object System.Text.UTF8Encoding($false))
)
Write-Host "Crypto Lab V0.3 READ-ONLY receipt created:" -ForegroundColor Green
Write-Host $OutputPath
Write-Host ("Matched tasks: " + $taskRows.Count + "; running: " +
    @($taskRows | Where-Object { $_.state -eq "Running" }).Count)
Write-Host ("Port 8787 listeners: " + @($listening).Count)
Write-Host "No commands, credentials, task actions, trading/account state, or DB secrets inspected."
