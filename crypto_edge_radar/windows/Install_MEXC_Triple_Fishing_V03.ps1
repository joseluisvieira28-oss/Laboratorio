param(
    [string]$BundleRoot = $PSScriptRoot,
    [string]$LegacyOptionsReceiptRoot = ""
)

$ErrorActionPreference = "Stop"
$taskName = "CryptoLab-Triple-Fishing-Operator-V03"
$runner = Join-Path $BundleRoot "Run_MEXC_Triple_Fishing_V03.ps1"
$overlayExe = Join-Path $BundleRoot "BuildOptionsCorrectionOverlayV01.exe"
$catalog = Join-Path $BundleRoot "OPTIONS_V21_HISTORICAL_FEE_CORRECTION_CATALOG_V01.json"
$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV03"
$archiveRoot = Join-Path $runtime "historical_options_receipts"
$stateDir = Join-Path $runtime "live_state"
$overlay = Join-Path $stateDir "OPTIONS_V21_PNL_CORRECTION_OVERLAY_V01.json"

if (-not (Test-Path -LiteralPath $runner)) { throw "Runner missing: $runner" }
if (-not (Test-Path -LiteralPath $overlayExe)) { throw "Overlay builder missing: $overlayExe" }
if (-not (Test-Path -LiteralPath $catalog)) { throw "Correction catalog missing: $catalog" }

if (-not $LegacyOptionsReceiptRoot) {
    $LegacyOptionsReceiptRoot = Join-Path $env:USERPROFILE "Desktop\OPTIONS_V21_FUTURES_ONLY_AUTOLIVE_V021\live_receipts\options_v21_futures"
}
if (-not (Test-Path -LiteralPath $LegacyOptionsReceiptRoot)) {
    throw "Legacy OPTIONS receipt root missing: $LegacyOptionsReceiptRoot"
}

New-Item -ItemType Directory -Force -Path $runtime,$stateDir | Out-Null
if (-not (Test-Path -LiteralPath $archiveRoot)) {
    New-Item -ItemType Directory -Force -Path $archiveRoot | Out-Null
    Copy-Item -Path (Join-Path $LegacyOptionsReceiptRoot "*") -Destination $archiveRoot -Recurse -Force
}
& $overlayExe --catalog $catalog --receipt-root $archiveRoot --out $overlay
if ($LASTEXITCODE -ne 0) { throw "Historical OPTIONS evidence failed identity/hash preparation." }

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -ExecutionPolicy Bypass -File " + [char]34 + $runner + [char]34) -WorkingDirectory $BundleRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Days 3650) -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Crypto Lab Triple Fishing V0.3 - BNB + OPTIONS + DH03 single-slot supervisor. Real-money entries require V0.3 ARMED marker." -Force | Out-Null
Start-ScheduledTask -TaskName $taskName
Write-Host "Installed and started UNARMED: $taskName"
Write-Host "Legacy BNB remains untouched. Do not arm V0.3 until Switch_From_BNB_To_Triple_V03.ps1 passes readiness."
