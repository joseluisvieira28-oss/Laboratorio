$ErrorActionPreference='Stop'
$src=Split-Path -Parent $PSScriptRoot
$dest=Join-Path $env:LOCALAPPDATA 'CryptoLab\ConvexRadarTrade'
$cmd=Get-Command py -ErrorAction SilentlyContinue
if (-not $cmd){throw 'Python 3 necessario. Instala Python 3 com launcher py -3.'}
& py -3 --version
if ($LASTEXITCODE -ne 0){throw 'Python 3 nao funciona'}
New-Item -ItemType Directory -Path (Join-Path $dest 'app') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $dest 'scripts') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $dest 'state') -Force | Out-Null
Copy-Item (Join-Path $src 'app\*.py') (Join-Path $dest 'app') -Force
Copy-Item (Join-Path $src 'scripts\*.ps1') (Join-Path $dest 'scripts') -Force
if(-not(Test-Path (Join-Path $dest 'config.json'))) { Copy-Item (Join-Path $src 'config.json') (Join-Path $dest 'config.json') }
# Do NOT copy a live authority from source ZIP and never replace existing risk settings silently.
& py -3 (Join-Path $dest 'app\engine.py') selftest
if($LASTEXITCODE -ne 0){throw 'Selftest falhou'}
Write-Host ('INSTALADO: '+$dest) -ForegroundColor Green
Write-Host 'Default: DISARMED. Continua no radar antigo sem alteracoes.'