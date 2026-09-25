param([switch]$Live)
$ErrorActionPreference="Stop"
$TaskName="CryptoEdgeRadarOptionsV21V03"
$watchdog=Join-Path $PSScriptRoot "RUN_MEXC_OPTIONS_24X7_V03.ps1"
if (-not (Test-Path $watchdog)) { throw "Watchdog missing: $watchdog" }
$Root=Split-Path -Parent $PSScriptRoot
$KillSwitch=Join-Path $Root "KILL_SWITCH"
if (Test-Path $KillSwitch) { throw "KILL_SWITCH is active. Remove it explicitly before arming live execution." }

$args='-NoProfile -ExecutionPolicy Bypass -File "' + $watchdog + '"'
if ($Live) { $args+=' -Live' }
$action=New-ScheduledTaskAction -Execute "powershell.exe" -Argument $args
$trigger=New-ScheduledTaskTrigger -AtLogOn
$settings=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Seconds 0)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Host ("PASS: " + $TaskName + " installed and started. Mode=" + $(if($Live){"LIVE_GATED"}else{"DRY_RUN"}))
Write-Host "PC must remain powered and awake through the UTC midnight execution window."
