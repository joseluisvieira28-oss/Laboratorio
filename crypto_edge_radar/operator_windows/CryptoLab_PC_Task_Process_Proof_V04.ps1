<#
Crypto Lab PC Evidence V0.4 — READ ONLY, no trade or collector activation.
Safe for existing MEXC operators. Inspects exact six task labels provided by
the operator, task ACTION EXECUTABLE *CLASS* only (never paths/arguments),
allowed process names' PID/start/memory, localhost Radar listener port 8787.
Does not query MEXC/account/DB, inspect secret files, read command lines,
read task Arguments, change tasks, stop processes, change energy policy or
send any external traffic. Output is one local JSON file only.
#>
[CmdletBinding()]
param([string]$OutputPath = "")

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$knownTasks = @(
    "CryptoLab-OPTIONS-V21-Futures-AutoLive",
    "CryptoLab-OPTIONS-V21-Telegram-Watcher",
    "CryptoLab-Triple-Fishing-Operator-V03",
    "CryptoEdgeRadarTruthCockpitV0145",
    "CryptoEdgeRadarV0144",
    "CryptoLab-BNB-Operator-AutoLive-V01"
)
$allowedClasses = @{
    "powershell.exe" = "POWERSHELL_HOST"
    "pwsh.exe" = "POWERSHELL_HOST"
    "cmd.exe" = "CMD_HOST"
    "python.exe" = "PYTHON_HOST"
    "pythonw.exe" = "PYTHON_HOST"
    "cryptoedgeradarnode.exe" = "RADAR_NODE"
    "wscript.exe" = "WINDOWS_SCRIPT_HOST"
    "cscript.exe" = "WINDOWS_SCRIPT_HOST"
    "node.exe" = "NODEJS_HOST"
}

function Get-ActionClass($taskAction) {
    # Evaluate locally; never serialize Execute path or Arguments.
    $exe = ""
    try { $exe = [System.IO.Path]::GetFileName(([string]$taskAction.Execute).Trim('"')).ToLowerInvariant() } catch {}
    if ($allowedClasses.ContainsKey($exe)) { return $allowedClasses[$exe] }
    return "OTHER_EXECUTABLE_CLASS_HIDDEN"
}
function SafeUtc($value) {
    try {
        if ($null -eq $value -or $value.Year -lt 2020) { return $null }
        return $value.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    } catch { return $null }
}
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $env:TEMP "CryptoLab_PC_Task_Process_Proof_V04.json"
}

$taskProof = @()
foreach ($label in $knownTasks) {
    $entry = [ordered]@{
        task_name = $label
        status = "NOT_FOUND_OR_NOT_READABLE"
        task_enabled = $null
        action_count = $null
        action_executable_classes = @()
        trigger_kinds = @()
        last_run_utc = $null
        last_result_code = $null
        unique_scientific_writer_proven = $false
    }
    try {
        $task = Get-ScheduledTask -TaskName $label -ErrorAction SilentlyContinue |
            Where-Object { $_.TaskName -eq $label } | Select-Object -First 1
        if ($null -ne $task) {
            $entry["status"] = [string]$task.State
            $entry["task_enabled"] = [bool]$task.Settings.Enabled
            $safeActions = @()
            foreach ($act in @($task.Actions)) { $safeActions += (Get-ActionClass $act) }
            $entry["action_count"] = $safeActions.Count
            $entry["action_executable_classes"] = $safeActions
            $kinds = @()
            foreach ($trigger in @($task.Triggers)) {
                $kind = [string]$trigger.CimClass.CimClassName
                if ($kind -notmatch "^MSFT_Task(Start|Boot|Logon|Time|Daily|Weekly|Monthly|Registration|Event|Idle|SessionStateChange|Calendar|Maintenance)") {
                    $kind = "OTHER_TRIGGER_TYPE_HIDDEN"
                }
                $kinds += $kind
            }
            $entry["trigger_kinds"] = $kinds
            try {
                $info = Get-ScheduledTaskInfo -InputObject $task -ErrorAction Stop
                $entry["last_run_utc"] = SafeUtc $info.LastRunTime
                $entry["last_result_code"] = [string]$info.LastTaskResult
            } catch {}
        }
    } catch { $entry["status"] = "TASK_METADATA_UNVERIFIED" }
    $taskProof += $entry
}

$processProof = @()
foreach ($name in @("CryptoEdgeRadarNode", "python", "pythonw", "powershell", "pwsh")) {
    try {
        foreach ($proc in @(Get-Process -Name $name -ErrorAction SilentlyContinue)) {
            $started = $null
            try { $started = SafeUtc $proc.StartTime } catch {}
            $processProof += [ordered]@{
                pid = [int]$proc.Id
                allowed_process_name = [string]$name
                started_utc = $started
                resident_memory_mb = [math]::Round(([double]$proc.WorkingSet64 / 1MB), 1)
            }
        }
    } catch {}
}
$processProof = @($processProof | Sort-Object allowed_process_name, pid)

$listeners = @()
try {
    $connections = @(Get-NetTCPConnection -LocalPort 8787 -ErrorAction SilentlyContinue |
        Where-Object { $_.State -eq "Listen" })
    foreach ($conn in $connections) {
        $owner = "UNKNOWN_OR_UNVERIFIED"
        try {
            $p = Get-Process -Id ([int]$conn.OwningProcess) -ErrorAction Stop
            if ($p.ProcessName -match "^(?i:CryptoEdgeRadarNode|python|pythonw|powershell|pwsh)$") {
                $owner = [string]$p.ProcessName
            } else { $owner = "OTHER_PROCESS_NAME_HIDDEN" }
        } catch {}
        $listeners += [ordered]@{
            port = 8787
            pid = [int]$conn.OwningProcess
            owner_name = $owner
            loopback_only = ($conn.LocalAddress -in @("127.0.0.1", "::1"))
        }
    }
} catch {}
$report = [ordered]@{
    schema = "CRYPTO_LAB_PC_TASK_PROCESS_PROOF_V0.4"
    checked_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    authority = "LOCAL_METADATA_READ_ONLY_NO_CAPITAL_OR_DB_WRITER"
    exact_six_tasks = $taskProof
    allowed_process_metadata = $processProof
    radar_listeners_8787 = $listeners
    last_action_arguments_read = $false
    task_action_paths_disclosed = $false
    process_command_lines_read = $false
    executable_files_opened = $false
    exchange_or_account_apis_called = $false
    database_connections_used = $false
    registry_or_scheduled_tasks_changed = $false
    process_started_or_stopped = $false
    external_network_requests = $false
    scientific_writer_count_proven = $false
    pc_collector_24_7_verified = $false
    no_duplicate_writer_proven = $false
    next_step = "OPERATOR_REVIEW_LOCAL_TASK_ROLE_AND_ACTIVITY__NO_NEW_COLLECTOR_YET"
}
$parent = Split-Path -Parent $OutputPath
if ([string]::IsNullOrWhiteSpace($parent) -or -not (Test-Path -LiteralPath $parent -PathType Container)) {
    throw "Receipt directory must already exist"
}
[System.IO.File]::WriteAllText(
    $OutputPath, (($report | ConvertTo-Json -Depth 12) + [Environment]::NewLine),
    (New-Object System.Text.UTF8Encoding($false))
)
Write-Host "CRYPTO LAB PC V0.4 — READ-ONLY FINISHED" -ForegroundColor Green
Write-Host ("Receipt: " + $OutputPath)
Write-Host ("Known task labels: " + @($taskProof).Count + "; allowed processes: " + @($processProof).Count + "; port 8787 listeners: " + @($listeners).Count)
Write-Host "NO task commands, API keys, orders, database passwords, or settings accessed."
