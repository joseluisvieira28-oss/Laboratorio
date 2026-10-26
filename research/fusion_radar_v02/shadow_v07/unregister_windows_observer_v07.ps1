$ErrorActionPreference='Stop'
$name='CryptoLab-Fusion-Shadow-V07-ReadOnly'
if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false
    Write-Host "Removed $name"
} else { Write-Host 'No Fusion Shadow scheduled task registered.' }
