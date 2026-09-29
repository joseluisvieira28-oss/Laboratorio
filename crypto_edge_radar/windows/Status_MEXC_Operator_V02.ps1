$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\OperatorFuturesV02"
$stateDir = Join-Path $runtime "live_state"
$armedPath = Join-Path $runtime "OPERATOR_FUTURES_V02_ARMED.json"
$killPath = Join-Path $runtime "OPERATOR_FUTURES_V02_KILL_SWITCH"
Write-Host "=== CONTROL ==="
Write-Host "ARMED       :" (Test-Path -LiteralPath $armedPath)
Write-Host "KILL SWITCH :" (Test-Path -LiteralPath $killPath)
Write-Host ""
$task = Get-ScheduledTask -TaskName "CryptoLab-BNB-Operator-AutoLive-V01" -ErrorAction SilentlyContinue
if ($null -ne $task) {
    Write-Host "=== TASK ==="
    $task | Select-Object TaskName,State | Format-List
    Get-ScheduledTaskInfo -TaskName $task.TaskName | Select-Object LastRunTime,LastTaskResult,NextRunTime | Format-List
}
foreach ($name in @("operator_ready_v02.json","bnb_operator_autolive_v01.json","operator_futures_engine_v02.json")) {
    $path = Join-Path $stateDir $name
    if (Test-Path -LiteralPath $path) {
        Write-Host "=== $name ==="
        Get-Content -LiteralPath $path -Raw
    }
}
