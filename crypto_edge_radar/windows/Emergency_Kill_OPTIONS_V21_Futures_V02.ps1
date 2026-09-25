$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$path = Join-Path $root "KILL_SWITCH"
[ordered]@{
    active = $true
    reason = "OPERATOR_EMERGENCY_KILL"
    created_at_utc = (Get-Date).ToUniversalTime().ToString("o")
} | ConvertTo-Json | Set-Content -Path $path -Encoding UTF8
Write-Host "KILL SWITCH ACTIVE."
Write-Host "No new Futures entries are allowed. If an OPTIONS V2.1 micro-live position is active, the agent will attempt a risk-reducing close."
