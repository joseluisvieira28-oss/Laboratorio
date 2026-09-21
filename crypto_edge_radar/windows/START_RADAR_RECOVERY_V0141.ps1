$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $Root "logs"
$DataDir = Join-Path $Root "data"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

$ExeCandidates = @(
    (Join-Path $Root "CryptoEdgeRadarNode.exe"),
    (Join-Path $Root "dist\CryptoEdgeRadarNode.exe")
)
$Exe = $ExeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Exe) {
    throw "CryptoEdgeRadarNode.exe not found under $Root or $Root\dist"
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

Log "=== Crypto Edge Radar V0.14.1 recovery launcher ==="
Log "Root: $Root"
Log "EXE: $Exe"

# Never kill arbitrary software on 8787.
if (PortListening) {
    Log "Port 8787 is already listening. Checking local Radar HTTP response..."
    try {
        $resp = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/" -TimeoutSec 4
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
            Log "Radar/local HTTP service is already reachable. Opening browser."
            Start-Process "http://127.0.0.1:$Port/"
            exit 0
        }
    }
    catch {
        throw "Port 8787 is occupied but the Radar HTTP check failed. Do not kill it automatically. Inspect with: Get-NetTCPConnection -LocalPort 8787 | Format-List *"
    }
}

# Stop only stale CryptoEdgeRadarNode processes from this product.
$old = Get-Process -Name "CryptoEdgeRadarNode" -ErrorAction SilentlyContinue
if ($old) {
    Log "Stopping stale CryptoEdgeRadarNode process(es)..."
    $old | Stop-Process -Force
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
            Start-Process "http://127.0.0.1:$Port/"
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
