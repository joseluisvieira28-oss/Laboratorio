$ErrorActionPreference = "Stop"
$taskName = "CryptoLab-Triple-Fishing-Operator-V04"
$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV04"
$kill = Join-Path $runtime "OPERATOR_FUTURES_V04_KILL_SWITCH"
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
Set-Content -LiteralPath $kill -Value ([DateTimeOffset]::UtcNow.ToString("o")) -Encoding ascii
Write-Host "V0.4 KILL SWITCH CREATED. New entries are blocked."
Write-Host "The V0.4 engine is designed to keep exit authority available and request exits for owned active positions."
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($null -ne $task -and $task.State -ne "Running") {
    Start-ScheduledTask -TaskName $taskName
    Write-Host "V0.4 task started so owned positions can be managed toward flat."
}
Write-Host "Do NOT delete the armed marker or stop the task until the ledger is empty and positions are reconciled."
