# Operator-run OPTIONAL registration. No admin and no credentials stored in task arguments.
# Swiss local triggers: 02:00, 03:00, 04:00 => UTC 01/02 for both CET and CEST.
# The Python code rejects all runs outside exact 01:00/02:00 UTC + 4 minutes.
# Runs only on 2026-10-27 .. 2026-11-09 UTC, no backfill.
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$script = Join-Path $root 'fusion_shadow_observer_v07.py'
if (!(Test-Path -LiteralPath $script)) { throw 'Missing observer source.' }
$launcher = (Get-Command py.exe -ErrorAction Stop).Source
$taskName = 'CryptoLab-Fusion-Shadow-V07-ReadOnly'
$ledger = Join-Path $root 'shadow_ledger_v07'
$arguments = ('"{0}" --cycle --notify-telegram --root "{1}"' -f $script,$ledger)
$action = New-ScheduledTaskAction -Execute $launcher -Argument $arguments -WorkingDirectory $root
$triggers = @(
  (New-ScheduledTaskTrigger -Daily -At '02:00'),
  (New-ScheduledTaskTrigger -Daily -At '03:00'),
  (New-ScheduledTaskTrigger -Daily -At '04:00')
)
foreach ($t in $triggers) { $t.EndBoundary = '2026-11-10T00:00:00' }
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable:$false -WakeToRun:$false -ExecutionTimeLimit (New-TimeSpan -Minutes 3)
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $triggers -Principal $principal -Settings $settings -Description 'Research-only BTC20 AVAX20 public snapshot + optional Telegram; no orders; expires 2026-11-10 local' -Force | Out-Null
Write-Host "Registered: $taskName (local 02:00, 03:00, 04:00, UTC checked inside script; stops 2026-11-10)"
Write-Host 'No market order, no private exchange API, no trading, no paid service.'
Write-Host 'For Telegram, set FUSION_TELEGRAM_BOT_TOKEN and FUSION_TELEGRAM_CHAT_ID in your Windows user environment variables; never put a token in this chat.'
