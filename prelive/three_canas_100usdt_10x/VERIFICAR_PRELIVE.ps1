# Crypto Lab / Tres Canas / 100 USDT / 10x
# PRELIVE OFFLINE READ-ONLY. No API, no scheduling, no orders, no keys.
# Run inside extracted archive: .\VERIFICAR_PRELIVE.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "CRYPTO LAB - 3 CANAS / 100 USDT / 10X - SEM ORDENS" -ForegroundColor Cyan
$python = Get-Command "py" -ErrorAction SilentlyContinue
if ($null -ne $python) {
    & py -3 "$root\preflight_risk_only.py" --config "$root\prelive_100usdt_configuration.json" --synthetic-only
} else {
    $python = Get-Command "python" -ErrorAction SilentlyContinue
    if ($null -eq $python) {
        throw "PYTHON_3_NAO_INSTALADO: instala Python 3.11+ e volta a executar"
    }
    & python "$root\preflight_risk_only.py" --config "$root\prelive_100usdt_configuration.json" --synthetic-only
}
if ($LASTEXITCODE -ne 0) {
    throw "RISK_PREFLIGHT_FAILED: consulta as mensagens acima"
}
Write-Host "RESULTADO: NO_LIVE_GO / SEM ORDENS - diagnostico apenas." -ForegroundColor Yellow
