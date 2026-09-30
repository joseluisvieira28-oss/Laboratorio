param([string]$BundleRoot = $PSScriptRoot)

$ErrorActionPreference = "Stop"
$legacyRuntime = Join-Path $env:LOCALAPPDATA "CryptoLab\OperatorFuturesV02"
$legacyArmed = Join-Path $legacyRuntime "OPERATOR_FUTURES_V02_ARMED.json"
$legacyTask = "CryptoLab-BNB-Operator-AutoLive-V01"

if (Test-Path -LiteralPath $legacyArmed) {
    Remove-Item -LiteralPath $legacyArmed -Force
    Write-Host "Legacy BNB DISARMED. Its supervisor remains running for any existing position."
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
Write-Host "TRIPLE FISHING V0.3 ARMED."
