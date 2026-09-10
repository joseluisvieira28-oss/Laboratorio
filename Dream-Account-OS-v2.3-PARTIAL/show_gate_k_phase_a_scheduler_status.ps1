$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Summary = Join-Path $Root 'show_gate_k_phase_a_summary_windows.bat'
$taskNames = @(
    'DreamAccountOS-GateK-PhaseA-MORNING',
    'DreamAccountOS-GateK-PhaseA-MIDDAY',
    'DreamAccountOS-GateK-PhaseA-EVENING'
)

Write-Host 'Gate K Phase A — Scheduler Status'
Write-Host '================================='
foreach ($taskName in $taskNames) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($null -eq $task) {
        Write-Host "$taskName : NOT INSTALLED"
        continue
    }
    $info = Get-ScheduledTaskInfo -TaskName $taskName
    Write-Host "$taskName"
    Write-Host "  State: $($task.State)"
    Write-Host "  Next run: $($info.NextRunTime)"
    Write-Host "  Last run: $($info.LastRunTime)"
    Write-Host "  Last result: $($info.LastTaskResult)"
}

$secretDir = Join-Path (Join-Path $Root 'gate_k_phase_a_evidence') 'secure'
$access = Join-Path $secretDir 'mexc_readonly_access.dpapi'
$secret = Join-Path $secretDir 'mexc_readonly_secret.dpapi'
Write-Host "DPAPI credential files present: $((Test-Path $access) -and (Test-Path $secret))"

if (Test-Path -LiteralPath $Summary) {
    Write-Host ''
    & cmd.exe /d /c ('"{0}"' -f $Summary)
}
