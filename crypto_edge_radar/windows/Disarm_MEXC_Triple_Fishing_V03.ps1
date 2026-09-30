$armed = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV03\OPERATOR_FUTURES_V03_ARMED.json"
if (Test-Path -LiteralPath $armed) { Remove-Item -LiteralPath $armed -Force }
Write-Host "Triple Fishing V0.3 new entries DISARMED. Supervisor remains running to manage any active position."
