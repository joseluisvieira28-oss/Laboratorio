$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $PSScriptRoot "Run_OPTIONS_V21_Futures_AutoLive_V02.ps1"
$exe = Join-Path $root "dist\OptionsV21FuturesAutoLive.exe"
$secretDir = Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
$keyPath = Join-Path $secretDir "mexc_api_key.dpapi"
$secretPath = Join-Path $secretDir "mexc_api_secret.dpapi"
$taskName = "CryptoLab-OPTIONS-V21-Futures-AutoLive"
$legacyTaskName = "CryptoLab-OPTIONS-V21-AutoLive"

if (-not (Test-Path $exe)) { throw "Missing executable: $exe" }
if (-not (Test-Path $runner)) { throw "Missing runner: $runner" }
if (-not (Test-Path $keyPath) -or -not (Test-Path $secretPath)) {
    throw "Existing MEXC DPAPI credentials were not found under LOCALAPPDATA."
}

if (Test-Path (Join-Path $root "AUTO_MICROLIVE_FUTURES_ARMED.json")) {
    throw "LEGACY_ARM_RECEIPT_PRESENT: refusing installer changes. Audit active orders/positions separately."
}

Get-ChildItem $root -Recurse -File | Unblock-File -ErrorAction SilentlyContinue

$legacy = Get-ScheduledTask -TaskName $legacyTaskName -ErrorAction SilentlyContinue
if ($legacy) {
    Stop-ScheduledTask -TaskName $legacyTaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $legacyTaskName -Confirm:$false
}

$current = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($current) {
    Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

New-Item -ItemType Directory -Force -Path (Join-Path $root "data") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $root "live_receipts\options_v21_futures") | Out-Null

# Installation is not trading authorization. Never create an armed receipt here.
# Refuse to rewrite existing schedules when an older armed receipt is present.
# The operator must verify and migrate that state with a separate audited procedure.

$actionArgs = '-NoProfile -ExecutionPolicy Bypass -File "' + $runner + '"'
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $actionArgs -WorkingDirectory $root
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -WakeToRun -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
Disable-ScheduledTask -TaskName $taskName | Out-Null
Start-Sleep -Seconds 3

$task = Get-ScheduledTask -TaskName $taskName
$info = Get-ScheduledTaskInfo -TaskName $taskName

Write-Host ""
Write-Host "========== OPTIONS V2.1 FUTURES-ONLY AUTO-MICROLIVE V0.2.1 =========="
Write-Host "Task                 : $taskName"
Write-Host "Task state           : $($task.State)"
Write-Host "Last task result     : $($info.LastTaskResult)"
Write-Host "Armed                : NO (installer never grants authority)"
Write-Host "Instrument           : BTC_USDT PERPETUAL ONLY"
Write-Host "LONG                 : NOT ARMED"
Write-Host "SHORT                : NOT ARMED"
Write-Host "Spot orders          : DISABLED / NOT INCLUDED"
Write-Host "Max live notional    : 10 USDT cap, scaled down by frozen parent weight"
Write-Host "Leverage             : exactly 1x"
Write-Host "Margin               : isolated only"
Write-Host "Exit                 : automatic +24h"
Write-Host "No-chase TTL         : 300 seconds"
Write-Host "Automatic sleep      : prevented while agent process is alive"
Write-Host "Kill switch          : $(Join-Path $root 'KILL_SWITCH')"
Write-Host "Status               : $(Join-Path $root 'options_v21_futures_autolive_status.json')"
Write-Host "======================================================================"
