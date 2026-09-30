$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV03"
$armed = Join-Path $runtime "OPERATOR_FUTURES_V03_ARMED.json"
$kill = Join-Path $runtime "OPERATOR_FUTURES_V03_KILL_SWITCH"
if (Test-Path -LiteralPath $armed) { Remove-Item -LiteralPath $armed -Force }
New-Item -ItemType File -Force -Path $kill | Out-Null
Write-Host "Triple Fishing V0.3 KILL SWITCH set and new entries disarmed."
Write-Host "Do NOT stop the supervisor: it must manage or exit any active operator position."
