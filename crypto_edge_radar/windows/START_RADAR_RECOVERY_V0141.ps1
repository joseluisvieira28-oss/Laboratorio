$ErrorActionPreference = "Stop"

$LauncherMutex = New-Object System.Threading.Mutex($false, "Local\CryptoEdgeRadarV0144Launcher")
if (-not $LauncherMutex.WaitOne(0)) {
    Write-Host "Another Radar launcher is already active. Refusing duplicate start."
    exit 0
}

$Root = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $Root "logs"
$DataDir = Join-Path $Root "data"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

$ExeCandidates = @(
    (Join-Path $Root "CryptoEdgeRadarNode\CryptoEdgeRadarNode.exe"),
    (Join-Path $Root "CryptoEdgeRadarNode.exe"),
    (Join-Path $Root "dist\CryptoEdgeRadarNode\CryptoEdgeRadarNode.exe"),
    (Join-Path $Root "dist\CryptoEdgeRadarNode.exe")
)
$Exe = $ExeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Exe) {
    throw "CryptoEdgeRadarNode.exe not found in the approved V0.14.4 onedir/root locations"
}

$Port = 8787
$Stdout = Join-Path $LogDir "radar_stdout.log"
$Stderr = Join-Path $LogDir "radar_stderr.log"
$LauncherLog = Join-Path $LogDir "radar_launcher.log"

function Log([string]$Message) {
    $line = "$(Get-Date -Format o) $Message"
    Add-Content -Path $LauncherLog -Value $line
    Write-Host $Message
}

function PortListening {
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
        return $null -ne $conn
    }
    catch {
        return $false
    }
}

Log "=== Crypto Edge Radar V0.14.4 live-state reconciliation launcher ==="
Log "Root: $Root"
Log "EXE: $Exe"

# Never kill arbitrary software on 8787. If an older CryptoEdgeRadarNode is
# occupying the port, identify it by process name and replace it only when the
# live /api/state proves it is not registry 3.7 / eight-motor canonical.
if (PortListening) {
    Log "Port 8787 is already listening. Verifying canonical Radar identity..."
    $canonicalAlreadyRunning = $false
    try {
        $state = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/state" -TimeoutSec 4
        $buildId = [string]$state.build_id
        $registryVersion = [string]$state.registry_version
        $focusExpected = [int]$state.registry.focus_expected
        $focusLoaded = [int]$state.registry.focus_loaded
        Log "Existing service reports build=$buildId registry=$registryVersion focus=$focusLoaded/$focusExpected"
        if (
            $buildId -eq "v0.14.4-win-cirv-eight-motor" -and
            $registryVersion -eq "3.7" -and
            $focusExpected -eq 8 -and
            $focusLoaded -eq 8
        ) {
            $canonicalAlreadyRunning = $true
        }
    }
    catch {
        Log "Existing port did not return a canonical Radar /api/state response."
    }

    if ($canonicalAlreadyRunning) {
        Log "PASS: canonical V0.14.4 registry 3.7 / 8-motor Radar is already running."
        if ($env:RADAR_NO_BROWSER -ne "1") { Start-Process "http://127.0.0.1:$Port/" }
        exit 0
    }

    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    $pids = @($listeners | Select-Object -ExpandProperty OwningProcess -Unique)
    if ($pids.Count -ne 1) {
        throw "Port 8787 is occupied by an unknown/multiple process set. Refusing automatic termination."
    }
    $owner = Get-Process -Id $pids[0] -ErrorAction SilentlyContinue
    $ownerPath = if ($null -eq $owner) { "" } else { [string]$owner.Path }
    $approvedPaths = @($ExeCandidates | ForEach-Object { [System.IO.Path]::GetFullPath($_) })
    if ($null -eq $owner -or $owner.ProcessName -ne "CryptoEdgeRadarNode" -or $approvedPaths -notcontains $ownerPath) {
        $name = if ($null -eq $owner) { "UNKNOWN" } else { $owner.ProcessName }
        throw "Port 8787 is occupied by $name at '$ownerPath' (PID $($pids[0])). Refusing to kill an unrelated or unverified process."
    }

    Log "Replacing stale/non-canonical CryptoEdgeRadarNode PID $($owner.Id)..."
    $owner | Stop-Process -Force
    Start-Sleep -Milliseconds 800
}

Remove-Item $Stdout,$Stderr -Force -ErrorAction SilentlyContinue

$env:RADAR_PROVIDER = "mexc_futures_public"
$env:RADAR_UNIVERSE_MODE = "core5"
$env:RADAR_DB = "data\radar_evidence.sqlite3"
$env:RADAR_STATUS = "data\radar_status.json"
$env:RADAR_NOTIFICATIONS = "data\radar_notifications.jsonl"

Log "Starting Radar. Browser will open ONLY after localhost:8787 responds."
$proc = Start-Process -FilePath $Exe -WorkingDirectory $Root -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -PassThru

$deadline = (Get-Date).AddSeconds(60)
$lastError = $null
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 500

    try {
        if ($proc.HasExited) {
            Log "Radar process exited early with code $($proc.ExitCode)."
            if (Test-Path $Stdout) {
                Write-Host "--- radar_stdout.log ---"
                Get-Content $Stdout -Tail 120
            }
            if (Test-Path $Stderr) {
                Write-Host "--- radar_stderr.log ---"
                Get-Content $Stderr -Tail 120
            }
            throw "RADAR_BOOT_FAILED_PROCESS_EXITED"
        }
    } catch [System.InvalidOperationException] {
        # Process state can race briefly on Windows; continue the probe loop.
    }

    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/" -TimeoutSec 2
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
            Log "PASS: Radar is responding on http://127.0.0.1:$Port/"
            Log "PID: $($proc.Id)"
            Log "stdout: $Stdout"
            Log "stderr: $Stderr"
            if ($env:RADAR_NO_BROWSER -ne "1") { Start-Process "http://127.0.0.1:$Port/" }
            exit 0
        }
    }
    catch {
        $lastError = $_.Exception.Message
    }
}

Log "FAIL: Radar did not become reachable within 60 seconds."
Log "Last HTTP error: $lastError"
if (Test-Path $Stdout) {
    Write-Host "--- radar_stdout.log ---"
    Get-Content $Stdout -Tail 120
}
if (Test-Path $Stderr) {
    Write-Host "--- radar_stderr.log ---"
    Get-Content $Stderr -Tail 120
}
if (Test-Path (Join-Path $DataDir "radar_status.json")) {
    Write-Host "--- data\radar_status.json ---"
    Get-Content (Join-Path $DataDir "radar_status.json") -Raw
}
if (Test-Path (Join-Path $DataDir "dh03_clock_preflight.json")) {
    Write-Host "--- data\dh03_clock_preflight.json ---"
    Get-Content (Join-Path $DataDir "dh03_clock_preflight.json") -Raw
}
throw "RADAR_BOOT_TIMEOUT"
