param(
    [string]$RadarRoot = "$env:USERPROFILE\Desktop\CryptoEdgeRadar_V01433_FINAL",
    [int]$ArmDays = 30
)
$ErrorActionPreference="Stop"
$DataDir=Join-Path $RadarRoot "data"
$ArmFile=Join-Path $DataDir "TIER2_AUTOLIVE_ARMED_V03.json"
$Ready=Join-Path $PSScriptRoot "Run_Tier2_MicroLive_Ready_Check_V03.ps1"

Write-Host ""
Write-Host "=== ARM TIER-2 AUTO-LIVE V0.3 ==="
Write-Host "Candidate: OPTIONS-SPOTPERP-001-V2.1 LONG -> MEXC Spot BTCUSDT"
Write-Host "Maximum notional: 10 USDT"
Write-Host "One concurrent position"
Write-Host "Daily realized-loss kill: 2 USDT"
Write-Host "Rolling 7-day realized-loss kill: 5 USDT"
Write-Host "No per-trade confirmation after this arming. Exact canonical gates still apply."
Write-Host ""

$answer=Read-Host "Type ARM LIVE to activate automatic real-order eligibility"
if ($answer -cne "ARM LIVE") {
    Write-Host "Not armed."
    exit 2
}

$proc=Start-Process powershell.exe -ArgumentList @(
    "-NoProfile","-ExecutionPolicy","Bypass","-File",$Ready,
    "-RadarRoot",$RadarRoot
) -NoNewWindow -Wait -PassThru
if ($proc.ExitCode -ne 0) {
    throw "V0.3 READY_CHECK did not pass. Auto-live remains disarmed."
}

New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
$now=(Get-Date).ToUniversalTime()
$expires=$now.AddDays($ArmDays)
$payload=[ordered]@{
    arming_id="TIER2_AUTOLIVE_ARMING_V0.3"
    status="ACTIVE"
    policy_id="TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24"
    candidate_id="OPTIONS-SPOTPERP-001-V2.1"
    allowed_lane="LONG_MEXC_SPOT_BTCUSDT"
    allow_real_orders=$true
    maximum_notional_usdt_equivalent=10.0
    maximum_total_account_exposure_usdt_equivalent=10.0
    maximum_concurrent_positions=1
    daily_realized_loss_kill_usdt=2.0
    rolling_7d_realized_loss_kill_usdt=5.0
    created_at_utc=$now.ToString("o")
    expires_at_utc=$expires.ToString("o")
}
$payload | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $ArmFile
Write-Host "PASS: AUTO-LIVE ARMED"
Write-Host "Arm file: $ArmFile"
Write-Host "Expires UTC: $($expires.ToString('o'))"
Write-Host "Run INSTALL_TIER2_AUTOLIVE_V03.ps1 to install/start the supervisor."
