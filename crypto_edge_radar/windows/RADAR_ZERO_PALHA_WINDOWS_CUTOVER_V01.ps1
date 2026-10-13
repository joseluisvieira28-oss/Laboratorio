[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$StageFolder,
    [switch]$Apply,
    [switch]$ConfirmedNoOpenFuturesPositionsAndOrders
)
$ErrorActionPreference = "Stop"

# Public Radar only: never touch other MEXC/Triple/Convex trading processes.
$desktop = Join-Path $env:USERPROFILE "Desktop"
$oldRoot = Join-Path $desktop "CryptoEdgeRadar_V01433_FINAL"
$oldExe = Join-Path $oldRoot "CryptoEdgeRadarNode\CryptoEdgeRadarNode.exe"
$newRoot = Join-Path $desktop "CryptoEdgeRadarZeroPalha_20261013"
$taskName = "CryptoEdgeRadarV0144"

$files = @(Get-ChildItem -LiteralPath $StageFolder -Filter "CryptoEdgeRadarNode.exe" -File -Recurse)
if ($files.Count -ne 1) { throw "STAGE_NOT_UNAMBIGUOUS: expected one CryptoEdgeRadarNode.exe" }
$source = $files[0].FullName
$manifest = "$source.sha256.txt"
if (-not (Test-Path -LiteralPath $manifest)) { throw "EXPECTED_BINARY_HASH_MISSING" }
$expected = [regex]::Match((Get-Content -LiteralPath $manifest -Raw),'sha256=([0-9a-fA-F]{64})').Groups[1].Value
if (-not $expected -or (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ine $expected) {
    throw "BINARY_HASH_MISMATCH"
}
$nodeTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($nodeTask -and $nodeTask.State -ne "Disabled") {
    throw "RADAR_WATCHDOG_MUST_BE_DISABLED_BEFORE_CUTOVER"
}
$optionsTask = Get-ScheduledTask -TaskName "CryptoLab-OPTIONS-V21-Futures-AutoLive" -ErrorAction SilentlyContinue
if ($optionsTask -and $optionsTask.State -ne "Disabled") {
    throw "OPTIONS_AUTOLIVE_RUNNING_OR_ENABLED: no cutover"
}
if (Test-Path (Join-Path $desktop "OPTIONS_V21_FUTURES_ONLY_AUTOLIVE_V021\AUTO_MICROLIVE_FUTURES_ARMED.json")) {
    throw "OPTIONS_ARMED_RECEIPT_PRESENT: no cutover"
}
if (Test-Path -LiteralPath $newRoot) {
    throw "DESTINATION_ALREADY_EXISTS: no overwriting previous diagnostic"
}
$oldProcess = @(Get-CimInstance Win32_Process -Filter "Name = 'CryptoEdgeRadarNode.exe'" -ErrorAction SilentlyContinue)
$expectedPath = [IO.Path]::GetFullPath($oldExe)
foreach ($p in $oldProcess) {
    if ([string]::IsNullOrWhiteSpace($p.ExecutablePath)) {
        throw "UNKNOWN_RADAR_PROCESS_PATH: cannot safely stop"
    }
    if (-not [string]::Equals([IO.Path]::GetFullPath($p.ExecutablePath),
                              $expectedPath,[StringComparison]::OrdinalIgnoreCase)) {
        throw "UNKNOWN_RADAR_PROCESS_PATH: cannot safely stop"
    }
}
$listener = @(Get-NetTCPConnection -LocalPort 8787 -State Listen -ErrorAction SilentlyContinue)
if ($listener.Count -gt 0) {
    $oldPids = @($oldProcess | ForEach-Object { [int]$_.ProcessId })
    foreach($l in $listener) {
        if ($oldPids -notcontains [int]$l.OwningProcess) {
            throw "PORT_8787_OWNED_BY_UNRECOGNIZED_PROCESS"
        }
    }
}

Write-Host "STAGING_HASH_PASS"
Write-Host "Old public Radar processes: $($oldProcess.Count)"
Write-Host "Radar task: $(if($nodeTask){$nodeTask.State}else{'Missing'})"
Write-Host "OPTIONS AutoLive task: $(if($optionsTask){$optionsTask.State}else{'Missing'})"
Write-Host "No independent trader processes are modified by this script."

if (-not $Apply) {
    Write-Host "PREVIEW_ONLY: No process changed. Rerun with -Apply and fresh account-flat confirmation."
    return
}
if (-not $ConfirmedNoOpenFuturesPositionsAndOrders) {
    throw "FRESH_OPERATOR_ACCOUNT_FLAT_CONFIRMATION_REQUIRED"
}
if (-not (Test-Path -LiteralPath $oldExe)) {
    throw "EXPECTED_OLD_PUBLIC_RADAR_EXE_NOT_FOUND"
}
$backup = Join-Path $desktop ("RADAR_ZERO_PALHA_BACKUP_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
New-Item -ItemType Directory -Path $backup -ErrorAction Stop | Out-Null
Copy-Item -LiteralPath $oldExe -Destination (Join-Path $backup "OldCryptoEdgeRadarNode.exe")
$oldRegistry = Join-Path $oldRoot "data\deployment_registry_v1.json"
if (Test-Path -LiteralPath $oldRegistry) {
    Copy-Item -LiteralPath $oldRegistry -Destination (Join-Path $backup "OldDeploymentRegistry.json")
}

foreach ($p in $oldProcess) {
    Stop-Process -Id ([int]$p.ProcessId) -ErrorAction Stop
}
Start-Sleep -Seconds 2
if (Get-Process CryptoEdgeRadarNode -ErrorAction SilentlyContinue) {
    throw "PUBLIC_RADAR_PROCESS_DID_NOT_STOP: no new launch"
}
New-Item -ItemType Directory -Path $newRoot -ErrorAction Stop | Out-Null
$target = Join-Path $newRoot "CryptoEdgeRadarNode.exe"
Copy-Item -LiteralPath $source -Destination $target
Copy-Item -LiteralPath $manifest -Destination (Join-Path $newRoot "CryptoEdgeRadarNode.exe.sha256.txt")
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ine $expected) {
    throw "INSTALLED_BINARY_HASH_MISMATCH"
}
$proc = Start-Process -FilePath $target -WorkingDirectory $newRoot -PassThru
$state = $null
for($i=0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 2
    try {
        $state = Invoke-RestMethod -Uri "http://127.0.0.1:8787/api/state" -TimeoutSec 3
        break
    } catch {}
}
if ($null -eq $state) { throw "ZERO_RADAR_DID_NOT_START: diagnostic only, old watcher not automatically restored" }
if ($state.system.health -ne "NO_ACTIVE_CANDIDATES" -or
    [int]$state.registry.focus_loaded -ne 0 -or
    [int]$state.registry.focus_expected -ne 0 -or
    $state.registry.operator_retirement_active -ne $true) {
    throw "ZERO_RADAR_VERIFICATION_FAILED: no old watcher restart"
}
Write-Host "ZERO_PALHA_PC_CUTOVER_PASS"
Write-Host "Public Radar PID: $($proc.Id)"
Write-Host "Archived executable: $backup"
Write-Host "Current diagnostic: http://127.0.0.1:8787/"
Write-Host "Independent trading operators were NOT stopped or deleted."
