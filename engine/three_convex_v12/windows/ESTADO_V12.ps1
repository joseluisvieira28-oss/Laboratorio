$name='CryptoLab-CONVEX-V12-FinalFour-ReadOnly'
$t=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if (-not $t) {Write-Output 'V12_NOT_INSTALLED';exit 2}
Write-Output ('V12_TASK: '+$t.State)
$p=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV12\data\V12_STATUS.json'
if (-not (Test-Path -LiteralPath $p)) {Write-Output 'V12_FIRST_CYCLE_PENDING';exit 0}
$s=Get-Content -LiteralPath $p -Raw | ConvertFrom-Json
$s | ConvertTo-Json -Depth 4
try {
    $age=([datetimeoffset]::UtcNow-[datetimeoffset]::Parse($s.checked_at_utc)).TotalMinutes
    Write-Output ('V12_AGE_MINUTES: '+[math]::Round($age,1))
    if ($age -gt 5 -or $s.status -ne 'V12_EXPERIMENTAL_READONLY') {Write-Output 'V12_HEALTH: INVESTIGATE';exit 2}
} catch {Write-Output 'V12_STATUS_UNPARSEABLE';exit 2}
Write-Output 'V12_MONITOR_RUNNING_NO_TRADE_AUTHORITY'
