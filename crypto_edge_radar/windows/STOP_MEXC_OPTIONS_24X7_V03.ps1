$ErrorActionPreference="Stop"
$TaskName="CryptoEdgeRadarOptionsV21V03"
$Root=Split-Path -Parent $PSScriptRoot
$KillSwitch=Join-Path $Root "KILL_SWITCH"

# Block every new entry first. Exit guards intentionally remain alive and
# interpret this file as an emergency risk-reducing exit instruction.
Set-Content -Path $KillSwitch -Value ("KILL_SWITCH_ON " + [DateTime]::UtcNow.ToString("o")) -Encoding ASCII

$task=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -ne $task) {
  Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Write-Host "SAFE STOP ACTIVE."
Write-Host "New entries are blocked by KILL_SWITCH."
Write-Host "Existing exit guards were NOT killed and may close active positions."
Write-Host ("Kill switch: " + $KillSwitch)
