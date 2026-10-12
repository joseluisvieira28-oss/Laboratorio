$ErrorActionPreference='Stop'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ConvexRadarTrade'
& py -3 (Join-Path $root 'app\engine.py') kill
Write-Host 'NOVAS ENTRADAS PARADAS. Se houver posicoes abertas, NAO parar o gestor de stops.' -ForegroundColor Yellow