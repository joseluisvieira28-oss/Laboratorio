param(
    [string]$InstallRoot = (Join-Path ([Environment]::GetFolderPath("Desktop")) "CryptoEdgeRadar_V01433_FINAL")
)

$ErrorActionPreference = "Stop"
$StageRoot = Split-Path -Parent $PSScriptRoot
$ExpectedBuild = "v0.14.4-win-cirv-eight-motor"
$ExpectedRegistry = "3.7"
$ExpectedFocus = 8
$Port = 8787

function Read-RadarState {
    try {
        return Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/state" -TimeoutSec 4
    }
    catch {
        return $null
    }
}

function Stop-KnownTask([string]$Name) {
    $task = Get-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        Stop-ScheduledTask -TaskName $Name -ErrorAction SilentlyContinue
    }
}

function Stop-VerifiedRadar {
    $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    if ($listeners.Count -eq 0) { return }
    $pids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
    if ($pids.Count -ne 1) {
        throw "Port 8787 has an unknown/multiple listener set. Refusing automatic stop."
    }
    $proc = Get-Process -Id $pids[0] -ErrorAction SilentlyContinue
    if ($null -eq $proc -or $proc.ProcessName -ne "CryptoEdgeRadarNode") {
        throw "Port 8787 is not owned by CryptoEdgeRadarNode. Refusing automatic stop."
    }

    $state = Read-RadarState
    if ($null -eq $state) {
        throw "Running Radar did not expose /api/state. Refusing automatic stop."
    }
    $build = [string]$state.build_id
    $registry = [string]$state.registry_version
    $loaded = [int]$state.registry.focus_loaded
    $expected = [int]$state.registry.focus_expected

    $isOldCanonical = (
        $build -eq "v0.14.3.3-win-single-instance-lock" -and
        $registry -eq "3.6" -and
        $loaded -eq 7 -and
        $expected -eq 7
    )
    $isNewCanonical = (
        $build -eq $ExpectedBuild -and
        $registry -eq $ExpectedRegistry -and
        $loaded -eq $ExpectedFocus -and
        $expected -eq $ExpectedFocus
    )
    if ($isNewCanonical) {
        Write-Host "PASS: V0.14.4 is already running. No replacement required."
        exit 0
    }
    if (-not $isOldCanonical) {
        throw "Running Radar identity is neither canonical V0.14.3.3 nor canonical V0.14.4. Refusing automatic replacement."
    }
    Stop-Process -Id $proc.Id -Force
    Start-Sleep -Milliseconds 800
}

$StageExe = Join-Path $StageRoot "CryptoEdgeRadarNode\CryptoEdgeRadarNode.exe"
$StageWindows = Join-Path $StageRoot "windows"
$StageAuthority = Join-Path $StageRoot "MEXC_FUTURES_STANDING_MICROLIVE_OPERATOR_AUTHORITY_V0.1.json"
if (-not (Test-Path $StageExe)) { throw "Validated V0.14.4 executable folder missing from extracted artifact." }
if (-not (Test-Path (Join-Path $StageWindows "START_RADAR_RECOVERY_V0141.ps1"))) { throw "Validated V0.14.4 launcher missing." }
if (-not (Test-Path (Join-Path $StageWindows "RUN_RADAR_24X7_V0144.ps1"))) { throw "V0.14.4 watchdog missing." }
if (-not (Test-Path (Join-Path $StageWindows "INSTALL_RADAR_AUTOSTART_V0144.ps1"))) { throw "V0.14.4 autostart installer missing." }
if (-not (Test-Path $StageAuthority)) { throw "Standing authority file missing from package." }
if (-not (Test-Path $InstallRoot)) { throw "Existing Radar install root not found: $InstallRoot" }

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$BackupRoot = Join-Path (Split-Path -Parent $InstallRoot) ("CryptoEdgeRadar_V01433_BACKUP_" + $timestamp)
$OldNode = Join-Path $InstallRoot "CryptoEdgeRadarNode"
$OldWindows = Join-Path $InstallRoot "windows"
$OldAuthority = Join-Path $InstallRoot "MEXC_FUTURES_STANDING_MICROLIVE_OPERATOR_AUTHORITY_V0.1.json"
$OldHashes = Join-Path $InstallRoot "CryptoEdgeRadarNode.sha256.txt"

Write-Host "=== Crypto Edge Radar V0.14.4 safe in-place upgrade ==="
Write-Host "Source: $StageRoot"
Write-Host "Destination: $InstallRoot"
Write-Host "Backup: $BackupRoot"

Stop-KnownTask "CryptoEdgeRadarV0143"
Stop-KnownTask "CryptoEdgeRadarV0144"
Stop-VerifiedRadar

New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
if (Test-Path $OldNode) { Copy-Item $OldNode (Join-Path $BackupRoot "CryptoEdgeRadarNode") -Recurse -Force }
if (Test-Path $OldWindows) { Copy-Item $OldWindows (Join-Path $BackupRoot "windows") -Recurse -Force }
if (Test-Path $OldAuthority) { Copy-Item $OldAuthority (Join-Path $BackupRoot "MEXC_FUTURES_STANDING_MICROLIVE_OPERATOR_AUTHORITY_V0.1.json") -Force }
if (Test-Path $OldHashes) { Copy-Item $OldHashes (Join-Path $BackupRoot "CryptoEdgeRadarNode.sha256.txt") -Force }

try {
    Remove-Item $OldNode -Recurse -Force -ErrorAction SilentlyContinue
    Copy-Item (Join-Path $StageRoot "CryptoEdgeRadarNode") $OldNode -Recurse -Force

    New-Item -ItemType Directory -Force -Path $OldWindows | Out-Null
    Copy-Item (Join-Path $StageWindows "*") $OldWindows -Recurse -Force
    Copy-Item $StageAuthority $OldAuthority -Force

    $stageHashes = Join-Path $StageRoot "CryptoEdgeRadarNode.sha256.txt"
    if (Test-Path $stageHashes) {
        Copy-Item $stageHashes $OldHashes -Force
    }

    # Validate packaged identity before restarting the service.
    $env:RADAR_PACKAGING_SELFTEST = "1"
    $self = (& (Join-Path $OldNode "CryptoEdgeRadarNode.exe")) | ConvertFrom-Json
    Remove-Item Env:RADAR_PACKAGING_SELFTEST -ErrorAction SilentlyContinue
    if ($self.status -ne "PASS") { throw "V0.14.4 package self-test failed after copy." }
    if ([string]$self.build_id -ne $ExpectedBuild) { throw "Unexpected V0.14.4 build identity after copy." }
    if ([string]$self.registry_version -ne $ExpectedRegistry) { throw "Unexpected registry after copy." }
    if ([int]$self.candidate_count -ne $ExpectedFocus) { throw "Unexpected motor count after copy." }
    if (-not $self.cirv_strategy_present -or -not $self.cirv_watcher_importable) { throw "CIRV package assertions failed after copy." }

    & (Join-Path $OldWindows "INSTALL_RADAR_AUTOSTART_V0144.ps1")

    $env:RADAR_NO_BROWSER = "1"
    & (Join-Path $OldWindows "START_RADAR_RECOVERY_V0141.ps1")
    Remove-Item Env:RADAR_NO_BROWSER -ErrorAction SilentlyContinue

    $deadline = (Get-Date).AddSeconds(45)
    $verified = $false
    $last = $null
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Seconds 1
        $last = Read-RadarState
        if ($null -eq $last) { continue }
        $cirv = [string]$last.local_runtime.cirv_status
        if (
            [string]$last.build_id -eq $ExpectedBuild -and
            [string]$last.registry_version -eq $ExpectedRegistry -and
            [int]$last.registry.focus_loaded -eq $ExpectedFocus -and
            [int]$last.registry.focus_expected -eq $ExpectedFocus -and
            $cirv -notin @("", "MISSING", "STARTING")
        ) {
            $verified = $true
            break
        }
    }
    if (-not $verified) {
        throw "V0.14.4 did not prove build/registry 8/8 plus CIRV runtime truth after restart."
    }

    Write-Host "PASS: V0.14.4 is live."
    Write-Host ("Build: " + [string]$last.build_id)
    Write-Host ("Registry: " + [string]$last.registry_version)
    Write-Host ("Focus: " + [string]$last.registry.focus_loaded + "/" + [string]$last.registry.focus_expected)
    Write-Host ("CIRV: " + [string]$last.local_runtime.cirv_status + " / " + [string]$last.local_runtime.cirv_runtime_phase)
    Write-Host ("Backup retained at: " + $BackupRoot)
    exit 0
}
catch {
    $upgradeError = $_.Exception.Message
    Write-Host "UPGRADE FAILED: $upgradeError"
    Write-Host "Rolling back to the preserved V0.14.3.3 package..."

    Stop-KnownTask "CryptoEdgeRadarV0144"
    try {
        $listeners = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
        foreach ($listener in $listeners) {
            $proc = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
            if ($null -ne $proc -and $proc.ProcessName -eq "CryptoEdgeRadarNode") {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {}

    Remove-Item $OldNode -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item $OldWindows -Recurse -Force -ErrorAction SilentlyContinue
    if (Test-Path (Join-Path $BackupRoot "CryptoEdgeRadarNode")) {
        Copy-Item (Join-Path $BackupRoot "CryptoEdgeRadarNode") $OldNode -Recurse -Force
    }
    if (Test-Path (Join-Path $BackupRoot "windows")) {
        Copy-Item (Join-Path $BackupRoot "windows") $OldWindows -Recurse -Force
    }
    if (Test-Path (Join-Path $BackupRoot "MEXC_FUTURES_STANDING_MICROLIVE_OPERATOR_AUTHORITY_V0.1.json")) {
        Copy-Item (Join-Path $BackupRoot "MEXC_FUTURES_STANDING_MICROLIVE_OPERATOR_AUTHORITY_V0.1.json") $OldAuthority -Force
    }
    if (Test-Path (Join-Path $BackupRoot "CryptoEdgeRadarNode.sha256.txt")) {
        Copy-Item (Join-Path $BackupRoot "CryptoEdgeRadarNode.sha256.txt") $OldHashes -Force
    }

    $oldInstaller = Join-Path $OldWindows "INSTALL_RADAR_AUTOSTART_V0143.ps1"
    $oldLauncher = Join-Path $OldWindows "START_RADAR_RECOVERY_V0141.ps1"
    if (Test-Path $oldInstaller) { & $oldInstaller }
    if (Test-Path $oldLauncher) {
        $env:RADAR_NO_BROWSER = "1"
        & $oldLauncher
        Remove-Item Env:RADAR_NO_BROWSER -ErrorAction SilentlyContinue
    }
    throw "V0.14.4 upgrade rolled back. Cause: $upgradeError"
}
