param([string]$BundleRoot = $PSScriptRoot)

$ErrorActionPreference = "Stop"
$taskName = "CryptoLab-Triple-Fishing-Operator-V04"
$runner = Join-Path $BundleRoot "Run_MEXC_Triple_Fishing_V04.ps1"
$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV04"
$armed = Join-Path $runtime "OPERATOR_FUTURES_V04_ARMED.json"
$authority = Join-Path $runtime "OPERATOR_FUTURES_GLOBAL_AUTHORITY_V04_ACTIVE.json"
$kill = Join-Path $runtime "OPERATOR_FUTURES_V04_KILL_SWITCH"

if (-not (Test-Path -LiteralPath $runner)) { throw "Runner missing: $runner" }
if (-not (Test-Path -LiteralPath $authority)) { throw "ACTIVE V0.4 authority missing." }
if (-not (Test-Path -LiteralPath $armed)) { throw "V0.4 armed marker missing." }
if (Test-Path -LiteralPath $kill) { throw "V0.4 kill switch is present." }

$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument ("-NoProfile -ExecutionPolicy Bypass -File " + [char]34 + $runner + [char]34) -WorkingDirectory $BundleRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Days 3650) -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Crypto Lab Triple Fishing V0.4 - three-slot small-fish supervisor. Requires hash-bound ACTIVE authority and armed marker." -Force | Out-Null
Start-ScheduledTask -TaskName $taskName
Write-Host ("Installed and started: " + $taskName)
