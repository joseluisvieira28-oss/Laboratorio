$ErrorActionPreference='Stop'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ConvexRadarTrade'
& py -3 (Join-Path $root 'app\engine.py') status
Get-ScheduledTask -TaskName 'CryptoLab-ConvexRadarTrade' -ErrorAction SilentlyContinue | Select-Object TaskName,State | Format-Table