param([string]$BundleRoot = $PSScriptRoot)

$ErrorActionPreference = "Stop"
$taskName = "CryptoLab-BNB-Operator-AutoLive-V01"
$runner = Join-Path $BundleRoot "Run_MEXC_BNB_Operator_AutoLive_V01.ps1"
if (-not (Test-Path -LiteralPath $runner)) { throw "Runner missing: $runner" }

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -ExecutionPolicy Bypass -File " + [char]34 + $runner + [char]34) -WorkingDirectory $BundleRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Days 3650) -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Crypto Lab BNB operator AutoLive V0.1 - 24x7 watcher. Real-money entries still require local ARMED marker and all runtime gates." -Force | Out-Null
Start-ScheduledTask -TaskName $taskName
Write-Host "Installed and started: $taskName"
Write-Host "This does NOT arm real-money entries. Run Ready_And_Arm_MEXC_Operator_V02.ps1 only after readiness passes."
