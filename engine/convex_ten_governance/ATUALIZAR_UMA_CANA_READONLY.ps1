# CRYPTO LAB 10 CANAS — CONTROLLED ONE-AT-A-TIME WINDOWS CUTOVER.
# PRE-FLIGHT BY DEFAULT. No source edits, no new trade authority, no private API calls from this script.
# Applies at most ONE observer V07/V11/V12; leaves other tasks and DPAPI secrets untouched.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][ValidateSet('V07','V11','V12')][string]$Version,
    [Parameter(Mandatory=$true)][string]$PackageDir,
    [ValidateSet('Preflight','Apply')][string]$Mode='Preflight',
    [string]$Approval='',
    [ValidateRange(60,600)][int]$ProbeSeconds=300
)
$ErrorActionPreference='Stop'
$expectedApproval='CONFIRMO_10_CANAS_READONLY'
$names=@{
    V07=@{ Task='CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly'; Dir='ThreeConvexV07'; Target='V07_Telegram_MEXC_Watcher.exe'; Source='V07_AUDIT_PREVIEW.exe'; Status='V07_WATCHER_STATUS.json'; Runner='RUN_V07_TELEGRAM.ps1'; Pin='99d06384268d649b2224a10fa9d231ad8ce78fb6ced8aaee4389f12d86e12e84' }
    V11=@{ Task='CryptoLab-Three-CONVEX-V11-Experimental-ReadOnly'; Dir='ThreeConvexV11'; Target='V11_Experimental_Signals.exe'; Source='V11_AUDIT_PREVIEW.exe'; Status='V11_STATUS.json'; Runner='RUN_V11.ps1'; Pin='8143e21de4cefb59c896fbb706d59def525ff9d459cdb36e182bf0bdd33db3bc' }
    V12=@{ Task='CryptoLab-CONVEX-V12-FinalFour-ReadOnly'; Dir='ThreeConvexV12'; Target='V12_FinalFour_Signals.exe'; Source='V12_FinalFour_Signals.exe'; Status='V12_STATUS.json'; Runner='RUN_V12.ps1'; Pin='0aa45a022de9c5e642316c757db72996c8bf126a3b6aed0247691852b6713bfe' }
}
$identity=$names[$Version]
$package=(Resolve-Path -LiteralPath $PackageDir -ErrorAction Stop).Path
$source=Join-Path $package $identity.Source
$root=Join-Path $env:LOCALAPPDATA ("CryptoLab\"+$identity.Dir)
$target=Join-Path $root $identity.Target
$runner=Join-Path $root $identity.Runner
$statusPath=Join-Path (Join-Path $root 'data') $identity.Status
$taskName=$identity.Task

function Assert-SourcePackage {
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {throw 'SOURCE_EXE_NOT_FOUND'}
    $actual=(Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($Version -in @('V07','V11')) {
        if ($actual -ne $identity.Pin) {throw 'SOURCE_EXE_NOT_AUDITED_V2'}
        $manifestPath=Join-Path $package 'BUILD_MANIFEST.json'
        if (-not (Test-Path -LiteralPath $manifestPath)) {throw 'V2_BUILD_MANIFEST_MISSING'}
        $manifest=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
        if ($manifest.source_commit -ne 'd31a4be82c8eed8d08cd9fba54567573b9153391') {throw 'V2_SOURCE_COMMIT_NOT_PINNED'}
        foreach($entry in $manifest.files) {
            if ([IO.Path]::GetFileName([string]$entry.name) -ne [string]$entry.name) {throw 'V2_MANIFEST_UNSAFE_FILENAME'}
            $file=Join-Path $package ([string]$entry.name)
            if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {throw 'V2_PACKAGE_FILE_MISSING'}
            if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) {throw 'V2_FILE_HASH_MISMATCH'}
        }
    } else {
        $hashPath=Join-Path $package 'SHA256_EXE.txt'
        if (-not (Test-Path -LiteralPath $hashPath -PathType Leaf)) {throw 'V12_MANIFEST_MISSING'}
        $expected=(Get-Content -LiteralPath $hashPath -Raw).Trim().ToLowerInvariant()
        if ($expected -notmatch '\A[a-f0-9]{64}\z' -or $actual -ne $expected -or $actual -ne $identity.Pin) {throw 'V12_EXE_NOT_AUDITED_PR239'}
        $run=Join-Path $package 'RUN_V12.ps1'
        if (-not (Test-Path -LiteralPath $run -PathType Leaf)) {throw 'V12_RUNNER_MISSING'}
        if (-not (Test-Path -LiteralPath (Join-Path $package 'AUDITAR_TELEGRAM_WINDOWS_READONLY.ps1') -PathType Leaf)) {throw 'V12_PR239_AUDIT_SIDECAR_MISSING'}
    }
    return $actual
}
function Assert-TaskAndFiles {
    $t=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
    if ($t.State -ne 'Running') {throw ('OBSERVER_NOT_RUNNING: '+[string]$t.State)}
    if (@($t.Actions).Count -ne 1) {throw 'UNEXPECTED_SCHEDULED_TASK_ACTIONS'}
    $action=$t.Actions[0]
    if ([IO.Path]::GetFileName([string]$action.Execute) -ine 'powershell.exe') {throw 'UNEXPECTED_SCHEDULED_TASK_LAUNCHER'}
    if ([string]$action.Arguments -notlike ('*'+$identity.Runner+'*')) {throw 'UNEXPECTED_RUNNER_SCRIPT'}
    if (-not (Test-Path -LiteralPath $target -PathType Leaf) -or -not (Test-Path -LiteralPath $runner -PathType Leaf)) {throw 'INSTALLED_BINARY_OR_RUNNER_MISSING'}
    if (-not (Test-Path -LiteralPath (Join-Path $root 'data') -PathType Container)) {throw 'INSTALLED_DATA_DIRECTORY_MISSING'}
    return $t
}
function Get-VersionProcessCount {
    return @(Get-Process -Name ([IO.Path]::GetFileNameWithoutExtension($identity.Target)) -ErrorAction SilentlyContinue).Count
}
function Wait-Exit {
    $deadline=[datetime]::UtcNow.AddSeconds(45)
    do {
        if ((Get-VersionProcessCount) -eq 0) {return}
        Start-Sleep -Seconds 1
    } while ([datetime]::UtcNow -lt $deadline)
    throw 'EXE_STILL_RUNNING_ABORT_DO_NOT_OVERWRITE'
}
function Stop-OnlyThisTask {
    Stop-ScheduledTask -TaskName $taskName -ErrorAction Stop
    Wait-Exit
}
function Health-After-Start([datetime]$startedUtc) {
    $deadline=[datetime]::UtcNow.AddSeconds($ProbeSeconds)
    do {
        Start-Sleep -Seconds 5
        $task=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
        if ($task.State -ne 'Running') {throw 'NEW_WATCHER_TASK_STOPPED'}
        if (Test-Path -LiteralPath $statusPath -PathType Leaf) {
            $stat=Get-Item -LiteralPath $statusPath
            if ($stat.LastWriteTimeUtc -ge $startedUtc.AddSeconds(-1)) {
                try {
                    $report=Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
                    $healthy=$false
                    switch($Version) {
                        'V07' { $healthy=($report.status -eq 'V07_TELEGRAM_PUBLIC_SIGNALS_AND_AUTH_MEXC_READONLY' -and $report.v5_public_source_ok -eq $true -and $report.account_snapshot_status -eq 'AUTHENTICATED_ACCOUNT_AND_PUBLIC_MARKET_READS_NO_LIVE_GO') }
                        'V11' { $healthy=($report.status -eq 'V11_EXPERIMENTAL_READONLY' -and $report.sources_ok -eq $true) }
                        'V12' { $healthy=($report.status -eq 'V12_EXPERIMENTAL_READONLY' -and $report.sources_ok -eq $true -and $report.total_inventory -eq 10 -and $report.orders_enabled -eq $false) }
                    }
                    if ($healthy) {
                        return [pscustomobject]@{Result='UPDATED_HEALTHY';Version=$Version;Task='Running';Status=[string]$report.status;ReportFileAgeSeconds=[math]::Round(([datetime]::UtcNow-$stat.LastWriteTimeUtc).TotalSeconds,1);SourceHash=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant();TradingAuthorized=$false}
                    }
                } catch [System.Management.Automation.RuntimeException] {
                    # The status may be written concurrently. Recheck on next poll.
                }
            }
        }
    } while ([datetime]::UtcNow -lt $deadline)
    throw 'NO_NEW_HEALTHY_STATUS_BEFORE_DEADLINE'
}

$pkgHash=Assert-SourcePackage
$installed=Assert-TaskAndFiles
$beforeHash=(Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
if ($beforeHash -eq $pkgHash) {
    [pscustomobject]@{Result='ALREADY_ON_VERIFIED_TARGET_HASH';Version=$Version;InstalledSha256=$beforeHash;NoTaskChanges=$true} | ConvertTo-Json
    exit 0
}
if ($Mode -eq 'Preflight') {
    [pscustomobject]@{Result='PREFLIGHT_PASS_NO_CHANGES';Version=$Version;Task=[string]$installed.State;
        CurrentSha256=$beforeHash;TargetSha256=$pkgHash;RunningExeProcesses=(Get-VersionProcessCount);
        WouldBackupData=$true;WouldRestartThisTaskOnly=$true;OtherObserversUnchanged=$true;
        Note='Apply requires -Mode Apply -Approval CONFIRMO_10_CANAS_READONLY'} | ConvertTo-Json
    exit 0
}
if ($Approval -cne $expectedApproval) {throw 'EXPLICIT_APPLY_APPROVAL_MISSING'}
$time=[datetime]::UtcNow
$backup=Join-Path $env:LOCALAPPDATA ('CryptoLab\CONVEX10_BACKUPS\'+$Version+'\'+$time.ToString("yyyyMMddTHHmmssZ"))
$taskWasStopped=$false
$binarySwapped=$false
$backupReady=$false
try {
    # First stop the ONE OBSERVER and wait for both PyInstaller processes to exit.
    $taskWasStopped=$true
    Stop-OnlyThisTask
    New-Item -ItemType Directory -Force -Path $backup | Out-Null
    Copy-Item -LiteralPath $target -Destination (Join-Path $backup 'original.exe') -ErrorAction Stop
    Copy-Item -LiteralPath $runner -Destination (Join-Path $backup 'original_runner.ps1') -ErrorAction Stop
    Copy-Item -LiteralPath (Join-Path $root 'data') -Destination (Join-Path $backup 'data') -Recurse -Force -ErrorAction Stop
    [pscustomobject]@{
        Version=$Version;Task=$taskName;CreatedUtc=$time.ToString('o');
        OriginalSha256=$beforeHash;TargetSha256=$pkgHash;StoppedForConsistentSqliteSnapshot=$true;
        StateRestorePolicy='PRESERVE_CURRENT_SQLITE_AFTER_ROLLBACK_TO_AVOID_DUPLICATE_NOTICES';
        ContainsDataDirectory=$true;ContainsCredentials=$false
    } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $backup 'UPGRADE_RECEIPT.json') -Encoding UTF8
    $backupReady=$true
    # Replace exactly the executable; the existing DPAPI loader remains untouched.
    $binarySwapped=$true
    Copy-Item -LiteralPath $source -Destination $target -Force -ErrorAction Stop
    if ($Version -eq 'V12') {
        # New V12 runner file is bundled and pinned to same release directory.
        Copy-Item -LiteralPath (Join-Path $package 'RUN_V12.ps1') -Destination $runner -Force -ErrorAction Stop
    }
    if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pkgHash) {throw 'INSTALLED_HASH_MISMATCH'}
    $started=[datetime]::UtcNow
    Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
    $health=Health-After-Start $started
    [pscustomobject]@{Result='CUTOVER_PASS';Version=$Version;Backup=$backup;
        OutageSeconds=[math]::Round(([datetime]::UtcNow-$time).TotalSeconds,1);
        Report=$health;OtherTasksModified=$false;TelegramE2EProven=$false} | ConvertTo-Json -Depth 6
} catch {
    $failure=$_.Exception.Message
    $recovery='NO_BACKUP_AVAILABLE'
    if ($backupReady -and $binarySwapped) {
        try {
            Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
            Wait-Exit
            Copy-Item -LiteralPath (Join-Path $backup 'original.exe') -Destination $target -Force -ErrorAction Stop
            Copy-Item -LiteralPath (Join-Path $backup 'original_runner.ps1') -Destination $runner -Force -ErrorAction Stop
            if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $beforeHash) {throw 'ROLLBACK_BINARY_HASH_MISMATCH'}
            # CRITICAL: Keep existing SQLite/outbox after brief rollout, even if
            # there may have been real sends, to avoid replaying Telegram alerts.
            # Additive schema migrations V2 don't require deletion of extra columns.
            Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
            $recovery='ORIGINAL_EXE_RESTART_REQUESTED_CURRENT_OUTBOX_PRESERVED'
        } catch {
            $recovery='ROLLBACK_FAILED_OPERATOR_ACTION_REQUIRED:'+($_.Exception.GetType().Name)
        }
    } elseif ($taskWasStopped) {
        try {
            # Stop-ScheduledTask can return with a still-running child EXE.
            # Do not restart while old child processes are present: never create twins.
            $remaining=(Get-VersionProcessCount)
            $state=[string](Get-ScheduledTask -TaskName $taskName -ErrorAction Stop).State
            if ($remaining -gt 0) {
                $recovery='CHILD_EXE_STILL_PRESENT_NO_RESTART_TO_AVOID_TWIN_OBSERVERS'
            } elseif ($state -eq 'Running') {
                $recovery='ORIGINAL_TASK_ALREADY_RUNNING_VERIFY_HEALTH'
            } else {
                Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
                $recovery='ORIGINAL_TASK_RESTART_REQUESTED'
            }
        } catch {
            $recovery='ORIGINAL_TASK_RESTART_FAILED_OPERATOR_ACTION_REQUIRED'
        }
    }
    [pscustomobject]@{Result='CUTOVER_FAIL_CLOSED';Version=$Version;Reason=$failure;
        Recovery=$recovery;Backup=if($backupReady){$backup}else{$null};OtherTasksModified=$false} | ConvertTo-Json
    throw 'CUTOVER_NOT_CONFIRMED_CHECK_RECOVERY_AND_TASK_STATUS'
}