$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\OperatorFuturesV02"
$armedPath = Join-Path $runtime "OPERATOR_FUTURES_V02_ARMED.json"
if (Test-Path -LiteralPath $armedPath) { Remove-Item -LiteralPath $armedPath -Force }
Write-Host "ARMED:" (Test-Path -LiteralPath $armedPath)
Write-Host "Supervisor remains running; an existing operator position, if any, remains managed to exit."
