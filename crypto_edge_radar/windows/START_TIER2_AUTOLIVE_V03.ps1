param(
    [string]$RadarRoot = "$env:USERPROFILE\Desktop\CryptoEdgeRadar_V01433_FINAL"
)
$ErrorActionPreference="Stop"
$PackRoot=Split-Path -Parent $PSScriptRoot
$Supervisor=Join-Path $PackRoot "dist\OptionsV21AutoLiveSupervisor.exe"
$DataDir=Join-Path $RadarRoot "data"
$Receipts=Join-Path $RadarRoot "live_receipts"
$ArmFile=Join-Path $DataDir "TIER2_AUTOLIVE_ARMED_V03.json"

if (-not (Test-Path $Supervisor)) { throw "OptionsV21AutoLiveSupervisor.exe missing" }
if (-not (Test-Path $ArmFile)) { throw "Auto-live is not armed. Run ARM_TIER2_AUTOLIVE_V03.ps1 first." }
if ([string]::IsNullOrWhiteSpace($env:MEXC_API_KEY) -or [string]::IsNullOrWhiteSpace($env:MEXC_API_SECRET)) {
    throw "MEXC_API_KEY / MEXC_API_SECRET must already exist in this local PowerShell process."
}
$env:CRYPTO_LAB_LIVE_EXECUTION_TOKEN="CRYPTO_LAB_TIER2_MICROLIVE_V0_3"
New-Item -ItemType Directory -Force -Path $DataDir,$Receipts | Out-Null
& $Supervisor --data-dir $DataDir --receipt-root $Receipts --arm-file $ArmFile --interval-seconds 0.25
exit $LASTEXITCODE
