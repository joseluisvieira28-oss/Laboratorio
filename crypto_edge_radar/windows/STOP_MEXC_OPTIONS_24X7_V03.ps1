$TaskName="CryptoEdgeRadarOptionsV21V03"
$task=Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($null -ne $task) {
  Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}
Get-Process -Name "MEXCTier2ExitGuard","MEXCTier2SpotExitGuard" -ErrorAction SilentlyContinue |
  Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "OPTIONS V2.1 V0.3 scheduled watchdog stopped/unregistered."
