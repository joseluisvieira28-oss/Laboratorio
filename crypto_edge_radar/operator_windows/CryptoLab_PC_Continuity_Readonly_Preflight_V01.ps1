<#
Crypto Lab Windows continuity preflight V0.1 — strict READ-ONLY.
Inspects OS capacity, DNS, available programs, sleep-policy readability, and
Task Scheduler presence. Does not install, alter Windows/Power settings,
start services, change task schedules, access MEXC/account/DB/bot secrets,
download code, send telemetry, trade, or create remote infrastructure.
Output only a local non-identifying JSON receipt.
#>
[CmdletBinding()]
param(
    [string]$OutputPath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function HasCommand([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}
function ByteGB([double]$B) {
    return [math]::Round(($B / 1GB), 2)
}
function TryDns([string]$HostName) {
    try {
        $addresses = [System.Net.Dns]::GetHostAddresses($HostName)
        if ($addresses.Count -gt 0) { return "DNS_RESOLVED_NO_API_REQUEST" }
        return "DNS_UNRESOLVED"
    } catch { return "DNS_UNRESOLVED" }
}

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $env:TEMP "CryptoLab_PC_Readonly_Preflight_V01.json"
}
$osname = "UNAVAILABLE"
$uptimeH = $null
$availableRam = $null
$diskGB = $null
$psVersion = $PSVersionTable.PSVersion.ToString()
try {
    $os = Get-CimInstance -ClassName Win32_OperatingSystem -ErrorAction Stop
    $osname = [string]$os.Caption
    $uptimeH = [math]::Round(((Get-Date) - $os.LastBootUpTime).TotalHours, 2)
    $availableRam = ByteGB ([double]$os.FreePhysicalMemory * 1KB)
} catch {}
try {
    $systemDrive = [string]$env:SystemDrive
    $disk = Get-CimInstance -ClassName Win32_LogicalDisk -Filter ("DeviceID='" + $systemDrive + "'") -ErrorAction Stop
    if ($null -ne $disk) { $diskGB = ByteGB ([double]$disk.FreeSpace) }
} catch {}

$python3 = "NOT_FOUND"
try {
    if (HasCommand "py.exe") {
        $ver = & py.exe -3 --version 2>&1
        if ($LASTEXITCODE -eq 0 -and ($ver -join " ") -match "^Python 3[.]") {
            $python3 = [string]($ver -join " ")
        }
    } elseif (HasCommand "python.exe") {
        $ver = & python.exe --version 2>&1
        if ($LASTEXITCODE -eq 0 -and ($ver -join " ") -match "^Python 3[.]") {
            $python3 = [string]($ver -join " ")
        }
    }
} catch {}

$powerSchemeAvailable = $false
$sleepConfigReadable = $false
try {
    if (HasCommand "powercfg.exe") {
        $null = & powercfg.exe /getactivescheme 2>&1
        $powerSchemeAvailable = $LASTEXITCODE -eq 0
        $null = & powercfg.exe /query SCHEME_CURRENT SUB_SLEEP STANDBYIDLE 2>&1
        $sleepConfigReadable = $LASTEXITCODE -eq 0
    }
} catch {}

$taskScan = "UNAVAILABLE"
$taskCounts = [ordered]@{}
try {
    if (HasCommand "Get-ScheduledTask") {
        $tasks = @(Get-ScheduledTask -ErrorAction Stop |
            Where-Object { $_.TaskName -match "(?i)cryptolab|crypto.lab|radar|fishing|mexc" })
        $taskScan = "READ_ONLY"
        $taskCounts["matching_task_count"] = @($tasks).Count
        $taskCounts["matching_running"] = @($tasks | Where-Object { $_.State -eq "Running" }).Count
        $taskCounts["matching_ready"] = @($tasks | Where-Object { $_.State -eq "Ready" }).Count
    }
} catch { $taskScan = "UNAVAILABLE" }

$dns = [ordered]@{
    github = TryDns "github.com"
    binance_vision = TryDns "data.binance.vision"
    render_public_shadow = TryDns "crypto-edge-radar-v05-canary.onrender.com"
    supabase = TryDns "jqzdvgjeuveiktftyrlz.supabase.co"
}

$report = [ordered]@{
    schema = "CRYPTO_LAB_WINDOWS_CONTINUITY_PREFLIGHT_V0.1"
    checked_utc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    authority = "LOCAL_READ_ONLY_NO_SECRET_OR_EXECUTION_ACCESS"
    os_caption = $osname
    powershell_version = $psVersion
    windows_uptime_hours = $uptimeH
    currently_free_ram_gb = $availableRam
    system_drive_free_gb = $diskGB
    suggested_disk_headroom_5gb = ($null -ne $diskGB -and $diskGB -ge 5)
    python3 = $python3
    git_present = (HasCommand "git.exe")
    power_scheme_query_available = $powerSchemeAvailable
    sleep_config_query_available = $sleepConfigReadable
    sleep_disabled_on_ac = "UNVERIFIED_REQUIRES_OPERATOR_CHECK"
    dns = $dns
    task_scheduler_scan = $taskScan
    task_counts = $taskCounts
    installed_worker_verified = $false
    durable_postgres_write_path_verified = $false
    single_writer_reconciliation_pass = $false
    stable_24h_power_internet_verified = $false
    trading_authority = "NONE"
    authenticated_account_reads = $false
    orders_created = $false
    scientific_rules_changed = $false
    secrets_collected = $false
    external_telemetry_sent = $false
    next_step = "RETURN_JSON_TO_OPERATOR_FOR_REVIEW__DO_NOT_START_DUPLICATE_COLLECTOR"
}
$json = $report | ConvertTo-Json -Depth 8
$parent = Split-Path -Parent $OutputPath
if ($parent -and -not (Test-Path -LiteralPath $parent)) {
    throw "Output directory must exist; script will not create new directories"
}
[System.IO.File]::WriteAllText($OutputPath, ($json + [Environment]::NewLine),
    (New-Object System.Text.UTF8Encoding($false)))
Write-Host "CRYPTO LAB: READ-ONLY PC PREFLIGHT GENERATED" -ForegroundColor Green
Write-Host ("Receipt: " + $OutputPath)
Write-Host ("OS: " + $osname + "; Python: " + $python3 + "; Disk: " + $diskGB + " GB")
Write-Host ("DNS reachable (name resolution only): " + (($dns.Values | Where-Object {$_ -eq "DNS_RESOLVED_NO_API_REQUEST"}).Count) + "/4")
Write-Host "Power 24/7, account secrets, exchange orders and single-writer cutover NOT tested."
Write-Host "Do NOT post any exchange or Telegram credentials; share only this JSON receipt."
