param(
    [switch]$RemoveCredentials
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$SecretDir = Join-Path (Join-Path $Root 'gate_k_phase_a_evidence') 'secure'
$taskNames = @(
    'DreamAccountOS-GateK-PhaseA-MORNING',
    'DreamAccountOS-GateK-PhaseA-MIDDAY',
    'DreamAccountOS-GateK-PhaseA-EVENING'
)

foreach ($taskName in $taskNames) {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "Removed task: $taskName"
    } else {
        Write-Host "Task not present: $taskName"
    }
}

if ($RemoveCredentials) {
    if (Test-Path -LiteralPath $SecretDir) {
        Remove-Item -LiteralPath $SecretDir -Recurse -Force
        Write-Host 'Removed DPAPI ciphertext credential directory.'
    }
} else {
    Write-Host 'DPAPI ciphertext credentials preserved. Use -RemoveCredentials to delete them.'
}

Write-Host 'Gate K Phase A scheduler is disabled. Existing SQLite evidence and logs were not deleted.'
