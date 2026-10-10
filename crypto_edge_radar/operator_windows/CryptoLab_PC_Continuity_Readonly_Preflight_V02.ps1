<#
Crypto Lab Windows continuity V0.2: local inventory ONLY.
NO changes to tasks, Windows sleep settings, network routes, users, or programs.
NO exchanges, wallet/account/API calls, database writes, token reads, or orders.
Task names are printed as labels only: never list Task Actions/Arguments.
Review JSON before sharing if task names contain anything personal.
#>
[CmdletBinding()]
param([string]$OutputPath = "")

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Inspect-Standby([string]$Alias) {
    $value = [ordered]@{
        queried = $false
        ac_sleep_minutes = $null
        dc_sleep_minutes = $null
        ac_result = "UNVERIFIED"
    }
    try {
        $lines = @(& powercfg.exe /query SCHEME_CURRENT SUB_SLEEP $Alias 2>&1)
        if ($LASTEXITCODE -ne 0) { return $value }
        $hex = @()
        foreach ($line in $lines) {
            foreach ($m in [regex]::Matches([string]$line, "0x[0-9A-Fa-f]{8}")) {
                $hex += [string]$m.Value
            }
        }
        # powercfg /query returns the two final AC/DC "current power setting
        # index" values, independent of display language (French/English).
        if ($hex.Count -lt 2) { return $value }
        $ac = [Convert]::ToInt64($hex[$hex.Count-2].Substring(2), 16)
        $dc = [Convert]::ToInt64($hex[$hex.Count-1].Substring(2), 16)
        $value["queried"] = $true
        $value["ac_sleep_minutes"] = [math]::Round(($ac / 60), 2)
        $value["dc_sleep_minutes"] = [math]::Round(($dc / 60), 2)
        $value["ac_result"] = if ($ac -eq 0) { "DISABLED_CURRENT_PLAN" } else { "ENABLED_CURRENT_PLAN" }
    } catch { }
    return $value
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $env:TEMP "CryptoLab_PC_Continuity_V02.json"
}

$totalRamGB = $null
$freeRamGB = $null
$uptimeHours = $null
try {
    $os = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
    $totalRamGB = [math]::Round(([double]$os.TotalVisibleMemorySize * 1KB / 1GB),2)
    $freeRamGB = [math]::Round(([double]$os.FreePhysicalMemory * 1KB / 1GB),2)
    $uptimeHours = [math]::Round(((Get-Date) - $os.LastBootUpTime).TotalHours,2)
} catch { }
$diskFreeGB = $null
try {
    $disk = Get-CimInstance Win32_LogicalDisk -Filter ("DeviceID='" + $env:SystemDrive + "'") -ErrorAction Stop
    if ($null -ne $disk) { $diskFreeGB = [math]::Round(([double]$disk.FreeSpace / 1GB),2) }
} catch { }

$sleep = Inspect-Standby "STANDBYIDLE"
$hibernate = Inspect-Standby "HIBERNATEIDLE"

$tasks = @()
$taskDiscovery = "UNVERIFIED"
try {
    $matched = @(Get-ScheduledTask -ErrorAction Stop | Where-Object {
        $_.TaskName -match "(?i)cryptolab|crypto.lab|radar|fishing|mexc"
    })
    $taskDiscovery = "READ_ONLY_LISTING"
    foreach ($task in $matched) {
        # Paths, command lines, Action.Arguments and stored credentials EXCLUDED.
        $tasks += [ordered]@{
            task_name = [string]$task.TaskName
            state = [string]$task.State
            enabled = [bool]$task.Settings.Enabled
            type_hint = if ($task.TaskName -match "(?i)mexc|futures|trading") {
                "POTENTIAL_EXCHANGE_EXECUTOR__DO_NOT_TOUCH"
            } elseif ($task.TaskName -match "(?i)radar|fishing|cryptolab|crypto.lab") {
                "CRYPTO_LAB_UNKNOWN_TASK__DO_NOT_TOUCH"
            } else { "UNKNOWN__DO_NOT_TOUCH" }
        }
    }
} catch {
    $taskDiscovery = "UNVERIFIED"
}
$tasks = @($tasks | Sort-Object task_name)

$processCounts = [ordered]@{}
foreach ($processName in @("python", "pythonw", "powershell", "pwsh")) {
    try {
        $processCounts[$processName] = @(Get-Process -Name $processName -ErrorAction SilentlyContinue).Count
    } catch { $processCounts[$processName] = $null }
}

$warnings = @()
if ($null -eq $freeRamGB -or $freeRamGB -lt 4) { $warnings += "RAM_HEADROOM_LT_4GB_OR_UNKNOWN" }
if ($null -eq $diskFreeGB -or $diskFreeGB -lt 20) { $warnings += "DISK_FREE_LT_20GB_OR_UNKNOWN" }
if ($sleep.ac_result -ne "DISABLED_CURRENT_PLAN") { $warnings += "AC_STANDBY_NOT_PROVEN_DISABLED" }
if ($hibernate.ac_result -ne "DISABLED_CURRENT_PLAN") { $warnings += "AC_HIBERNATE_NOT_PROVEN_DISABLED" }
if (@($tasks | Where-Object {$_.state -eq "Running"}).Count -gt 0) {
    $warnings += "EXISTING_RUNNING_CRYPTO_TASK_REQUIRES_OPERATOR_RECONCILIATION"
}
if ($taskDiscovery -ne "READ_ONLY_LISTING") { $warnings += "TASK_DISCOVERY_UNVERIFIED" }

$report = [ordered]@{
    schema = "CRYPTO_LAB_WINDOWS_CONTINUITY_V0.2"
    checked_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    authority = "READ_ONLY_DIAGNOSTIC__NO_EXECUTION"
    physical_continuity_verified = $false
    windows_uptime_hours = $uptimeHours
    # Uptime is NOT an independent proof of no standby/wake interruptions.
    uptime_is_proof_of_24h_collection = $false
    total_ram_gb = $totalRamGB
    free_ram_gb = $freeRamGB
    system_drive_free_gb = $diskFreeGB
    power = [ordered]@{
        sleep_idle_ac = $sleep
        hibernate_idle_ac = $hibernate
        power_always_on_24h_confirmed = $false
    }
    scheduled_task_scan = $taskDiscovery
    scheduled_task_count = $tasks.Count
    matching_tasks = $tasks
    process_name_counts_only = $processCounts
    warnings = $warnings
    unique_scientific_writer_verified = $false
    task_actions_or_arguments_read = $false
    live_orders_read_or_modified = $false
    api_tokens_read = $false
    external_telemetry_sent = $false
    files_modified_outside_receipt = $false
    exchange_mutation_performed = $false
    next_step = "RECONCILE_EXISTING_TASKS_AND_POWER_HEADROOM_BEFORE_SHADOW_WRITER"
}
$json = $report | ConvertTo-Json -Depth 12
$directory = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
    throw "Directory for receipt must already exist"
}
[System.IO.File]::WriteAllText($OutputPath, ($json+[Environment]::NewLine),
    (New-Object System.Text.UTF8Encoding($false)))
Write-Host ("CONTINUITY V0.2: READ-ONLY: " + $OutputPath) -ForegroundColor Green
Write-Host ("Task names only: " + $tasks.Count + " | Running: " + @($tasks | Where-Object {$_.state -eq "Running"}).Count)
Write-Host ("Free RAM: " + $freeRamGB + " GB | Free drive: " + $diskFreeGB + " GB")
Write-Host ("Power standby AC: " + $sleep.ac_result + "; hibernate AC: " + $hibernate.ac_result)
Write-Host "Nothing was stopped, started, reconfigured, authenticated or traded."
