$name='CryptoLab-Three-CONVEX-V11-Experimental-ReadOnly'
$t=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if ($t) {Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue;Disable-ScheduledTask -TaskName $name | Out-Null}
Write-Output 'V11_DISABLED_V07_UNCHANGED'
