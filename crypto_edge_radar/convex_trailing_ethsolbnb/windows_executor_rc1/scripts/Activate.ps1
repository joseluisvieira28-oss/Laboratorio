$ErrorActionPreference='Stop'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ConvexRadarTrade'
$launcher=Join-Path $root 'scripts\Run-With-Secrets.ps1'
if(-not(Test-Path $launcher)){throw 'Executa 01_INSTALAR.cmd primeiro.'}
# Avoid concurrent LIVE ownership by existing scheduled task. Never terminate or disarm an old manager.
$conflicts=@(Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object {
   $_.TaskName -match 'CryptoLab|MEXC|TripleFishing' -and $_.TaskName -ne 'CryptoLab-ConvexRadarTrade' -and $_.State -eq 'Running'
})
if($conflicts.Count -gt 0){throw ('OLD_RADAR_RUNNING_STOP_AND_RECONCILE_BY_OWNER: '+($conflicts.TaskName -join ', '))}
& powershell.exe -NoProfile -File $launcher -Command arm
if($LASTEXITCODE -ne 0){throw 'LIVE nao foi armado'}
Write-Host 'LIVE ARMADO LOCALMENTE. Nao e certificacao de fills nem garantia de SL.' -ForegroundColor Yellow