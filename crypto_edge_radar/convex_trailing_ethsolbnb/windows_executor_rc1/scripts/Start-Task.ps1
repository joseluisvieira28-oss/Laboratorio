$ErrorActionPreference='Stop'
$root=Join-Path $env:LOCALAPPDATA 'CryptoLab\ConvexRadarTrade'
$launcher=Join-Path $root 'scripts\Run-With-Secrets.ps1'
if(-not(Test-Path $launcher)){throw 'Executa 01_INSTALAR.cmd primeiro.'}
$task='CryptoLab-ConvexRadarTrade'
$arg='-NoProfile -File "'+$launcher+'" -Command run'
$act=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arg -WorkingDirectory $root
$trig=New-ScheduledTaskTrigger -AtLogOn
$setting=New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName $task -Action $act -Trigger $trig -Settings $setting -Description 'Convex ETH/SOL/BNB Radar engine. New entries require separately armed authority. Manages owned stops after kill.' -Force | Out-Null
Start-ScheduledTask -TaskName $task
Write-Host 'Tarefa Windows instalada. Observacao ate ARMAR. PC acordado e login sao necessarios.'