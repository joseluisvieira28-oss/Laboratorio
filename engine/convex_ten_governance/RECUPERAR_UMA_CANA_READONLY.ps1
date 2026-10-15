# Manual rollback of one read-only CONVEX observer AFTER cutover, preserving existing SQLite.
# Does not restore stale queue snapshots to avoid duplicate Telegram observations.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('V07','V11','V12')][string]$Version,
    [Parameter(Mandatory=$true)][string]$BackupDir,
    [Parameter(Mandatory=$true)][string]$Approval
)
$ErrorActionPreference='Stop'
if ($Approval -cne 'CONFIRMO_ROLLBACK_UMA_CANA') {throw 'ROLLBACK_EXPLICIT_APPROVAL_MISSING'}
$map=@{
    V07=@{Task='CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly';Dir='ThreeConvexV07';Exe='V07_Telegram_MEXC_Watcher.exe';Runner='RUN_V07_TELEGRAM.ps1'}
    V11=@{Task='CryptoLab-Three-CONVEX-V11-Experimental-ReadOnly';Dir='ThreeConvexV11';Exe='V11_Experimental_Signals.exe';Runner='RUN_V11.ps1'}
    V12=@{Task='CryptoLab-CONVEX-V12-FinalFour-ReadOnly';Dir='ThreeConvexV12';Exe='V12_FinalFour_Signals.exe';Runner='RUN_V12.ps1'}
}
$def=$map[$Version]
$allowedBase=[IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA ('CryptoLab\CONVEX10_BACKUPS\'+$Version)))
$resolved=(Resolve-Path -LiteralPath $BackupDir -ErrorAction Stop).Path
$resolved=[IO.Path]::GetFullPath($resolved)
if (-not $resolved.StartsWith(($allowedBase.TrimEnd('\')+'\'),[StringComparison]::OrdinalIgnoreCase)) {throw 'BACKUP_NOT_UNDER_APPROVED_CRYPTOLAB_ROOT'}
$receipt=Join-Path $resolved 'UPGRADE_RECEIPT.json'
$old=Join-Path $resolved 'original.exe'
$oldRunner=Join-Path $resolved 'original_runner.ps1'
if (-not (Test-Path -LiteralPath $receipt -PathType Leaf) -or -not (Test-Path -LiteralPath $old -PathType Leaf) -or -not (Test-Path -LiteralPath $oldRunner -PathType Leaf)) {throw 'ROLLBACK_RECEIPT_OR_BINARY_MISSING'}
$r=Get-Content -LiteralPath $receipt -Raw | ConvertFrom-Json
if ($r.Version -ne $Version -or $r.Task -ne $def.Task -or $r.ContainsDataDirectory -ne $true) {throw 'ROLLBACK_RECEIPT_IDENTITY_MISMATCH'}
$oldHash=(Get-FileHash -LiteralPath $old -Algorithm SHA256).Hash.ToLowerInvariant()
if ($r.OriginalSha256 -ne $oldHash) {throw 'ROLLBACK_BACKUP_HASH_MISMATCH'}
$t=Get-ScheduledTask -TaskName $def.Task -ErrorAction Stop
if ($t.State -notin @('Ready','Running')) {throw 'ROLLBACK_UNEXPECTED_TASK_STATE'}
$root=Join-Path $env:LOCALAPPDATA ('CryptoLab\'+$def.Dir)
$exe=Join-Path $root $def.Exe
$runner=Join-Path $root $def.Runner
$wasStarted=$false
try {
    if ($t.State -eq 'Running') {
        Stop-ScheduledTask -TaskName $def.Task -ErrorAction Stop
    }
    $deadline=[datetime]::UtcNow.AddSeconds(45)
    while (@(Get-Process -Name ([IO.Path]::GetFileNameWithoutExtension($def.Exe)) -ErrorAction SilentlyContinue).Count -gt 0) {
        if ([datetime]::UtcNow -ge $deadline) {throw 'ROLLBACK_ACTIVE_EXE_BLOCKED'}
        Start-Sleep -Seconds 1
    }
    Copy-Item -LiteralPath $old -Destination $exe -Force -ErrorAction Stop
    Copy-Item -LiteralPath $oldRunner -Destination $runner -Force -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $oldHash) {throw 'ROLLBACK_INSTALLED_HASH_MISMATCH'}
    Start-ScheduledTask -TaskName $def.Task -ErrorAction Stop
    $wasStarted=$true
    [pscustomobject]@{Result='ROLLBACK_EXECUTABLE_RESTORED';Version=$Version;RestoredHash=$oldHash;
        TaskRestartRequested=$true;SQLiteRestored=$false;
        Next='Verify fresh task health with ESTADO_10_CANAS_READONLY.ps1 before claiming operational.'} | ConvertTo-Json
} catch {
    [pscustomobject]@{Result='ROLLBACK_INCOMPLETE_FAIL_CLOSED';Version=$Version;
        Reason=$_.Exception.Message;TaskRestarted=$wasStarted;Next='Inspect task and outbox locally. Do not repeat automatically.'} | ConvertTo-Json
    throw
}