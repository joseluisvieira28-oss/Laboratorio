$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$path = Join-Path $root "KILL_SWITCH"
if (Test-Path $path) { Remove-Item $path -Force }
Write-Host "KILL SWITCH CLEARED. OPTIONS V2.1 Futures auto-microlive eligibility restored."
