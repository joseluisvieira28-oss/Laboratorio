$name='CryptoLab-Three-CONVEX-V11-Experimental-ReadOnly'
$t=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if (-not $t) {Write-Output 'V11_NOT_INSTALLED';exit 2}
Write-Output ('V11_TASK: '+$t.State)
$p=Join-Path $env:LOCALAPPDATA 'CryptoLab\ThreeConvexV11\data\V11_STATUS.json'
if (Test-Path $p) {Get-Content $p -Raw} else {Write-Output 'V11_FIRST_CYCLE_PENDING'}
Write-Output 'V07_UNMODIFIED; ZERO_MEXC_POST'
