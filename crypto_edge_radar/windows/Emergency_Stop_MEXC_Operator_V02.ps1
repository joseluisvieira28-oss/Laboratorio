$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\OperatorFuturesV02"
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$killPath = Join-Path $runtime "OPERATOR_FUTURES_V02_KILL_SWITCH"
@{ created_at_local = (Get-Date).ToString("o"); reason = "OPERATOR_REQUESTED_EMERGENCY_STOP" } | ConvertTo-Json | Set-Content -LiteralPath $killPath -Encoding UTF8
Write-Host "KILL SWITCH: ON"
Write-Host "The running supervisor will submit a governed emergency exit for its own active operator position."
