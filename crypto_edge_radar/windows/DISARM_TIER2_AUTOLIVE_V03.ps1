param(
    [string]$RadarRoot = "$env:USERPROFILE\Desktop\CryptoEdgeRadar_V01433_FINAL"
)
$ErrorActionPreference="Continue"
$ArmFile=Join-Path $RadarRoot "data\TIER2_AUTOLIVE_ARMED_V03.json"
if (Test-Path $ArmFile) {
    $arm=Get-Content $ArmFile -Raw | ConvertFrom-Json
    $arm.status="DISARMED"
    $arm.disarmed_at_utc=(Get-Date).ToUniversalTime().ToString("o")
    $arm | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $ArmFile
}
Get-Process -Name "OptionsV21AutoLiveSupervisor" -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "AUTO-LIVE DISARMED. No new entries can be created."
Write-Host "If a live position already exists, inspect its exit/reconciliation state separately."
