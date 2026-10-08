# Read-only local health report. Does not launch, arm, disarm or contact MEXC.
param([int]$MaxHeartbeatAgeSeconds = 60)
$ErrorActionPreference = "Stop"
$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV03"
$stateDir = Join-Path $runtime "live_state"
$statusPath = Join-Path $stateDir "triple_fishing_operator_v03.json"
$logPath = Join-Path $stateDir "launcher_events_v03.jsonl"
$taskName = "CryptoLab-Triple-Fishing-Operator-V03"
$proc = @(Get-Process -Name 'MEXCTripleFishingOperatorV03' -ErrorAction SilentlyContinue)
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
$taskInfo = if ($task) { Get-ScheduledTaskInfo -InputObject $task -ErrorAction SilentlyContinue } else { $null }
$payload = $null
$heartbeatAge = $null
$jsonValid = $false
if (Test-Path -LiteralPath $statusPath -PathType Leaf) {
    try {
        $payload = Get-Content -LiteralPath $statusPath -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
        $ts = ([DateTimeOffset]::Parse([string]$payload.checked_at_utc)).UtcDateTime
        $heartbeatAge = [math]::Round(([DateTime]::UtcNow - $ts).TotalSeconds,3)
        $jsonValid = $true
    } catch { $jsonValid = $false }
}
$latestStage = $null
$latestResult = $null
$latestCode = $null
if (Test-Path -LiteralPath $logPath -PathType Leaf) {
    try {
        $lines = @(Get-Content -LiteralPath $logPath -Tail 10 -ErrorAction Stop)
        foreach ($line in ($lines | Select-Object -Last 10)) {
            try {
                $row = $line | ConvertFrom-Json -ErrorAction Stop
                if ($row.schema -eq 'TRIPLE_LAUNCHER_DIAGNOSTIC_V0.1') {
                    $latestStage = $row.stage
                    $latestResult = $row.result
                    $latestCode = $row.numeric_code
                }
            } catch { }
        }
    } catch { }
}
[pscustomobject]@{
    CheckedAtUtc = [DateTime]::UtcNow.ToString('o')
    TaskState = if ($task) { [string]$task.State } else { 'NOT_REGISTERED' }
    LastTaskResult = if ($taskInfo) { $taskInfo.LastTaskResult } else { $null }
    ProcessCount = $proc.Count
    ArmedMarker = Test-Path -LiteralPath (Join-Path $runtime 'OPERATOR_FUTURES_V03_ARMED.json')
    KillSwitch = Test-Path -LiteralPath (Join-Path $runtime 'OPERATOR_FUTURES_V03_KILL_SWITCH')
    GlobalSlotFile = Test-Path -LiteralPath (Join-Path $stateDir 'GLOBAL_POSITION_SLOT_V03.json')
    StateJsonValid = $jsonValid
    StateStatus = if ($jsonValid) { [string]$payload.status } else { 'UNAVAILABLE' }
    HeartbeatAgeSeconds = $heartbeatAge
    HeartbeatFresh = [bool]($jsonValid -and $heartbeatAge -ge 0 -and $heartbeatAge -le $MaxHeartbeatAgeSeconds)
    LastLauncherStage = $latestStage
    LastLauncherResult = $latestResult
    LastLauncherCode = $latestCode
    AccountPositionsVerified = 'NOT_CHECKED'
    AccountOrdersVerified = 'NOT_CHECKED'
}
# Never infer the state of positions/orders from local markers.
