$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $PSScriptRoot "Run_OPTIONS_V21_AutoLive.ps1"
$exe = Join-Path $root "dist\OptionsV21AutoLive.exe"
$secretDir = Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
$keyPath = Join-Path $secretDir "mexc_api_key.dpapi"
$secretPath = Join-Path $secretDir "mexc_api_secret.dpapi"
$taskName = "CryptoLab-OPTIONS-V21-AutoLive"

if (-not (Test-Path $exe)) { throw "Missing executable: $exe" }
if (-not (Test-Path $runner)) { throw "Missing runner: $runner" }
if (-not (Test-Path $keyPath) -or -not (Test-Path $secretPath)) { throw "Existing MEXC DPAPI credentials were not found under LOCALAPPDATA." }

Get-ChildItem $root -Recurse -File | Unblock-File -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path (Join-Path $root "data") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $root "live_receipts\options_v21") | Out-Null

$armed = [ordered]@{
    authority = "TIER2-AUTO-MICROLIVE-POLICY-V2.0-FROZEN-2026-09-25"
    strategy_id = "OPTIONS-SPOTPERP-001-V2.1"
    max_notional_usdt = 10
    leverage = 1
    maximum_concurrent_positions = 1
    installed_by_windows_user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    armed_at_utc = (Get-Date).ToUniversalTime().ToString("o")
}
$armed | ConvertTo-Json -Depth 4 | Set-Content -Path (Join-Path $root "AUTO_MICROLIVE_ARMED.json") -Encoding UTF8

$actionArgs = '-NoProfile -ExecutionPolicy Bypass -File "' + $runner + '"'
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArgs -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Start-ScheduledTask -TaskName $taskName
Start-Sleep -Seconds 2

$task = Get-ScheduledTask -TaskName $taskName
$info = Get-ScheduledTaskInfo -TaskName $taskName

Write-Host ""
Write-Host "================ OPTIONS V2.1 AUTO-MICROLIVE INSTALL ================"
Write-Host "Task                 : $taskName"
Write-Host "Task state           : $($task.State)"
Write-Host "Last task result     : $($info.LastTaskResult)"
Write-Host "Armed                : YES"
Write-Host "Max live notional    : 10 USDT (weighted down by frozen strategy weight)"
Write-Host "Futures leverage     : 1x isolated only"
Write-Host "LONG route           : MEXC Spot BTCUSDT"
Write-Host "SHORT route          : MEXC Futures BTC_USDT"
Write-Host "Exit                 : automatic +24h"
Write-Host "No-chase TTL         : 300 seconds"
Write-Host "Kill switch          : $(Join-Path $root 'KILL_SWITCH')"
Write-Host "Status               : $(Join-Path $root 'options_v21_autolive_status.json')"
Write-Host "======================================================================"
Write-Host ""
Write-Host "The task runs only under this Windows user so the existing DPAPI secrets remain user-bound."
Write-Host "Do not delete the package folder while the task is installed."
