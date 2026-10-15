$name='CryptoLab-CONVEX-V12-FinalFour-ReadOnly'
$t=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if ($t) {
    Stop-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    Disable-ScheduledTask -TaskName $name | Out-Null
}
Write-Output 'V12_STOPPED_AND_DISABLED_V07_V11_UNCHANGED'
