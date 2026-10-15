# Experimental signals V11 — independent read-only scheduled task.
$ErrorActionPreference='Stop'
$v07='CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly'
$name='CryptoLab-Three-CONVEX-V11-Experimental-ReadOnly'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV11'
$exe=Join-Path $PSScriptRoot 'V11_Experimental_Signals.exe'
$hash=Join-Path $PSScriptRoot 'SHA256_EXE.txt'
if (-not (Get-ScheduledTask -TaskName $v07 -ErrorAction SilentlyContinue)) {throw 'V07_EXISTING_TASK_NOT_FOUND'}
if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {throw 'V11_ALREADY_INSTALLED'}
if (-not (Test-Path $exe) -or -not (Test-Path $hash)) {throw 'V11_PACKAGE_INCOMPLETE'}
$expected=(Get-Content $hash -Raw).Trim().ToLowerInvariant()
$actual=(Get-FileHash $exe -Algorithm SHA256).Hash.ToLowerInvariant()
if ($expected -ne $actual) {throw 'V11_SHA256_MISMATCH'}
$secret=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07\secrets\telegram_bot_token.dpapi'
$chat=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07\secrets\telegram_chat_id.txt'
if (-not (Test-Path $secret) -or -not (Test-Path $chat)) {throw 'V07_TELEGRAM_SECRETS_NOT_FOUND'}
New-Item -ItemType Directory -Path $root,(Join-Path $root 'data') -Force | Out-Null
Copy-Item $exe (Join-Path $root 'V11_Experimental_Signals.exe') -Force
Copy-Item (Join-Path $PSScriptRoot 'RUN_V11.ps1') (Join-Path $root 'RUN_V11.ps1') -Force
$action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -ExecutionPolicy Bypass -File "'+(Join-Path $root 'RUN_V11.ps1')+'"') -WorkingDirectory $root
$identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$trigger=New-ScheduledTaskTrigger -AtLogOn -User $identity
$settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Description 'CONVEX V11 experimental public signals / Telegram outbound / zero orders' | Out-Null
Start-ScheduledTask -TaskName $name
Write-Output 'V11_EXPERIMENTAL_MONITOR_STARTED_V07_UNCHANGED'
