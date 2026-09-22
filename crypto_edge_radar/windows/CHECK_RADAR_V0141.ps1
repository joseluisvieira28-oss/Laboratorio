$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Write-Host "=== Crypto Edge Radar local diagnostic ==="
Write-Host "Time: $(Get-Date -Format o)"
Write-Host "Root: $Root"
Write-Host ""

Write-Host "--- Process ---"
Get-Process -Name "CryptoEdgeRadarNode" -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,StartTime,Path | Format-List

Write-Host "--- Port 8787 ---"
Get-NetTCPConnection -LocalPort 8787 -ErrorAction SilentlyContinue | Select-Object State,LocalAddress,LocalPort,OwningProcess,RemoteAddress,RemotePort | Format-Table -AutoSize

Write-Host "--- HTTP ---"
try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8787/" -TimeoutSec 4
    Write-Host "HTTP PASS: $($resp.StatusCode)"
} catch {
    Write-Host "HTTP FAIL: $($_.Exception.Message)"
}

foreach ($rel in @(
    "data\radar_status.json",
    "data\dh03_clock_preflight.json",
    "data\dh03_local_status.json",
    "data\forward_local_supervisor_status.json",
    "data\cirv_local_status.json",
    "data\render_sentinel_supervisor_status.json"
)) {
    $p = Join-Path $Root $rel
    if (Test-Path $p) {
        Write-Host ""
        Write-Host "--- $rel ---"
        Get-Content $p -Raw
    }
}

foreach ($rel in @("logs\radar_stdout.log","logs\radar_stderr.log","logs\radar_launcher.log")) {
    $p = Join-Path $Root $rel
    if (Test-Path $p) {
        Write-Host ""
        Write-Host "--- $rel (tail) ---"
        Get-Content $p -Tail 80
    }
}
