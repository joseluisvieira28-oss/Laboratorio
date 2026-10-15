# V12 installation: ONLY four experimental public signals, no broker orders.
$ErrorActionPreference='Stop'
$v07='CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly'
$v11='CryptoLab-Three-CONVEX-V11-Experimental-ReadOnly'
$v12='CryptoLab-CONVEX-V12-FinalFour-ReadOnly'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV12'
$exe=Join-Path $PSScriptRoot 'V12_FinalFour_Signals.exe'
$manifest=Join-Path $PSScriptRoot 'SHA256_EXE.txt'
if (-not (Get-ScheduledTask -TaskName $v07 -ErrorAction SilentlyContinue) -or -not (Get-ScheduledTask -TaskName $v11 -ErrorAction SilentlyContinue)) {
    throw 'EXISTING_V07_V11_TASKS_REQUIRED_NO_REPLACEMENT'
}
if (Get-ScheduledTask -TaskName $v12 -ErrorAction SilentlyContinue) {throw 'V12_ALREADY_INSTALLED_DO_NOT_DUPLICATE'}
if (-not (Test-Path -LiteralPath $exe -PathType Leaf) -or -not (Test-Path -LiteralPath $manifest -PathType Leaf)) {throw 'V12_PACKAGE_MISSING'}
$expected=(Get-Content -LiteralPath $manifest -Raw).Trim().ToLowerInvariant()
$actual=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
if ($expected -ne $actual) {throw 'V12_PACKAGE_SHA256_MISMATCH'}
$secretRoot=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV07\secrets'
if (-not (Test-Path (Join-Path $secretRoot 'telegram_bot_token.dpapi')) -or -not (Test-Path (Join-Path $secretRoot 'telegram_chat_id.txt'))) {throw 'V07_TELEGRAM_CREDENTIALS_NOT_FOUND'}
New-Item -ItemType Directory -Force -Path $root,(Join-Path $root 'data') | Out-Null
Copy-Item -LiteralPath $exe -Destination (Join-Path $root 'V12_FinalFour_Signals.exe') -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'RUN_V12.ps1') -Destination (Join-Path $root 'RUN_V12.ps1') -Force
$arg='-NoProfile -ExecutionPolicy Bypass -File "'+(Join-Path $root 'RUN_V12.ps1')+'"'
$action=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arg -WorkingDirectory $root
$identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$trigger=New-ScheduledTaskTrigger -AtLogOn -User $identity
$settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $v12 -Action $action -Trigger $trigger -Settings $settings -Description 'V12: FINAL 4 of 10 CONVEX public experimental alerts. ZERO ORDERS.' | Out-Null
Start-ScheduledTask -TaskName $v12
Write-Output 'V12_INSTALLED_4_NEW_LANES_LIMIT_10_TOTAL_V07_V11_UNCHANGED'
Write-Output 'NO_TRADING_OR_MEXC_PRIVATE_API'
