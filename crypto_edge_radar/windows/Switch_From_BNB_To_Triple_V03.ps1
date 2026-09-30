param([string]$BundleRoot = $PSScriptRoot)

$ErrorActionPreference = "Stop"
$legacyRuntime = Join-Path $env:LOCALAPPDATA "CryptoLab\OperatorFuturesV02"
$legacyArmed = Join-Path $legacyRuntime "OPERATOR_FUTURES_V02_ARMED.json"
$legacyTask = "CryptoLab-BNB-Operator-AutoLive-V01"
$legacyOptionsTask = "CryptoLab-OPTIONS-V21-Futures-AutoLive"
$legacyOptionsArmed = Join-Path $env:USERPROFILE "Desktop\OPTIONS_V21_FUTURES_ONLY_AUTOLIVE_V021\AUTO_MICROLIVE_FUTURES_ARMED.json"

if (Test-Path -LiteralPath $legacyArmed) {
    Remove-Item -LiteralPath $legacyArmed -Force
    Write-Host "Legacy BNB DISARMED. Its supervisor remains running for any existing position."
}
if (Test-Path -LiteralPath $legacyOptionsArmed) {
    Remove-Item -LiteralPath $legacyOptionsArmed -Force
    Write-Host "Legacy OPTIONS DISARMED. Its supervisor remains untouched until triple readiness passes."
}
Start-Sleep -Seconds 2

& (Join-Path $BundleRoot "Ready_And_Arm_MEXC_Triple_Fishing_V03.ps1") -BundleRoot $BundleRoot
if ($LASTEXITCODE -ne 0) {
    throw "Triple readiness did not pass. Legacy BNB remains disarmed; do not rearm blindly."
}

try {
    Get-ScheduledTask -TaskName $legacyTask -ErrorAction Stop | Out-Null
    Stop-ScheduledTask -TaskName $legacyTask -ErrorAction SilentlyContinue
    Disable-ScheduledTask -TaskName $legacyTask | Out-Null
    Write-Host "Legacy BNB task stopped and disabled after clean triple readiness."
}
catch {
    Write-Host "Legacy BNB task not found or already disabled."
}
try {
    Get-ScheduledTask -TaskName $legacyOptionsTask -ErrorAction Stop | Out-Null
    Stop-ScheduledTask -TaskName $legacyOptionsTask -ErrorAction SilentlyContinue
    Disable-ScheduledTask -TaskName $legacyOptionsTask | Out-Null
    Write-Host "Legacy OPTIONS task stopped and disabled after clean triple readiness."
}
catch {
    Write-Host "Legacy OPTIONS task not found or already disabled."
}
Write-Host "TRIPLE FISHING V0.3 ARMED."
