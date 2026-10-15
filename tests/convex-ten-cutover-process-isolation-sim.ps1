# Unit-simulated Windows process lifecycle. NEVER invokes actual Task Scheduler / Stop-Process.
$ErrorActionPreference='Stop'
$source=Join-Path (Split-Path -Parent $PSScriptRoot) 'engine/convex_ten_governance/ATUALIZAR_UMA_CANA_READONLY.ps1'
$errors=$null; $tokens=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'CUTOVER_PARSER_FAILED'}
$wanted=@('Get-VersionProcesses','Get-VersionProcessCount','Assert-VerifiedProcesses','ProcessFingerprint','Wait-Exit','Stop-OnlyThisTask')
$defs=@($ast.FindAll({param($x) $x -is [Management.Automation.Language.FunctionDefinitionAst]},$true))
foreach($name in $wanted) {
    $def=$defs|Where-Object{$_.Name -eq $name}|Select-Object -First 1
    if(-not $def){throw "CUTOVER_FN_MISSING:$name"}
    Invoke-Expression $def.Extent.Text
}
$identity=@{Target='V07_Telegram_MEXC_Watcher.exe'}
$taskName='CryptoLab-Three-CONVEX-V07-Telegram-ReadOnly'
$target='C:\Temp\CryptoLab\V07_Telegram_MEXC_Watcher.exe'
$expected=[IO.Path]::GetFullPath($target)
$script:simProcs=@()
$script:taskState='Running'
$script:killed=@()
$script:replaceOnStop=$false
function Get-CimInstance {
    [CmdletBinding()]
    param([string]$ClassName,[string]$Filter)
    if ($Filter -match '^ProcessId=([0-9]+)
function Get-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    return [pscustomobject]@{State=$script:taskState}
}
function Stop-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    $script:taskState='Ready'
    if($script:replaceOnStop) {
        $script:simProcs=@(
            [pscustomobject]@{ProcessId=1201;ExecutablePath=$expected;CreationDate=[datetime]'2026-10-15T12:00:00Z'},
            [pscustomobject]@{ProcessId=1303;ExecutablePath=$expected;CreationDate=[datetime]'2026-10-15T12:00:05Z'}
        )
    }
}
function Stop-Process {
    [CmdletBinding()]
    param([int]$Id,[switch]$Force)
    $script:killed+= $Id
    $script:simProcs=@($script:simProcs|Where-Object{$_.ProcessId -ne $Id})
}
function Start-Sleep {
    [CmdletBinding()]
    param([int]$Seconds)
}
function Reset-Simulation {
    $script:taskState='Running'
    $script:killed=@()
    $script:replaceOnStop=$false
    $script:simProcs=@(
        [pscustomobject]@{ProcessId=1201;ExecutablePath=$expected;CreationDate=[datetime]'2026-10-15T12:00:00Z'},
        [pscustomobject]@{ProcessId=1202;ExecutablePath=$expected;CreationDate=[datetime]'2026-10-15T12:00:05Z'}
    )
}
Reset-Simulation
Stop-OnlyThisTask
if($script:taskState -ne 'Ready' -or $script:simProcs.Count -ne 0 -or ($script:killed -join ',') -ne '1201,1202') {
    throw 'SIM_ORPHAN_RECOVERY_DID_NOT_STOP_EXACTLY_EXPECTED_TWO'
}
Write-Output 'SIM_TASK_READY_ORPHANED_BOTH_EXES_REAPED_PASS'
Reset-Simulation
$script:simProcs[1].ExecutablePath='C:\Different\UNTRUSTED.exe'
$blocked=$false
try { Stop-OnlyThisTask } catch { $blocked=$_.Exception.Message -match 'EXE_PROCESS_PATH_MISMATCH_DO_NOT_KILL' }
if(-not $blocked -or $script:killed.Count -ne 0 -or $script:taskState -ne 'Running') {
    throw 'SIM_UNTRUSTED_PATH_DID_NOT_FAIL_BEFORE_STOP'
}
Write-Output 'SIM_WRONG_EXECUTABLE_PATH_FAIL_CLOSED_PASS'
Reset-Simulation
$script:replaceOnStop=$true
$blocked=$false
try { Stop-OnlyThisTask } catch { $blocked=$_.Exception.Message -match 'PROCESS_IDENTITY_CHANGED_ABORT_NO_KILL' }
if(-not $blocked -or $script:killed.Count -ne 0) {throw 'SIM_PID_REPLACEMENT_NOT_FAIL_CLOSED'}
Write-Output 'SIM_PID_SWAP_AFTER_TASK_STOP_FAIL_CLOSED_PASS'
exit 0
) {
        $wantedId=[int]$Matches[1]
        return @($script:simProcs|Where-Object{$_.ProcessId -eq $wantedId})
    }
    return $script:simProcs
}
function Get-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    return [pscustomobject]@{State=$script:taskState}
}
function Stop-ScheduledTask {
    [CmdletBinding()]
    param([string]$TaskName)
    $script:taskState='Ready'
    if($script:replaceOnStop) {
        $script:simProcs=@(
            [pscustomobject]@{ProcessId=1201;ExecutablePath=$expected;CreationDate=[datetime]'2026-10-15T12:00:00Z'},
            [pscustomobject]@{ProcessId=1303;ExecutablePath=$expected;CreationDate=[datetime]'2026-10-15T12:00:05Z'}
        )
    }
}
function Stop-Process {
    [CmdletBinding()]
    param([int]$Id,[switch]$Force)
    $script:killed+= $Id
    $script:simProcs=@($script:simProcs|Where-Object{$_.ProcessId -ne $Id})
}
function Start-Sleep {
    [CmdletBinding()]
    param([int]$Seconds)
}
function Reset-Simulation {
    $script:taskState='Running'
    $script:killed=@()
    $script:replaceOnStop=$false
    $script:simProcs=@(
        [pscustomobject]@{ProcessId=1201;ExecutablePath=$expected;CreationDate=[datetime]'2026-10-15T12:00:00Z'},
        [pscustomobject]@{ProcessId=1202;ExecutablePath=$expected;CreationDate=[datetime]'2026-10-15T12:00:05Z'}
    )
}
Reset-Simulation
Stop-OnlyThisTask
if($script:taskState -ne 'Ready' -or $script:simProcs.Count -ne 0 -or ($script:killed -join ',') -ne '1201,1202') {
    throw 'SIM_ORPHAN_RECOVERY_DID_NOT_STOP_EXACTLY_EXPECTED_TWO'
}
Write-Output 'SIM_TASK_READY_ORPHANED_BOTH_EXES_REAPED_PASS'
Reset-Simulation
$script:simProcs[1].ExecutablePath='C:\Different\UNTRUSTED.exe'
$blocked=$false
try { Stop-OnlyThisTask } catch { $blocked=$_.Exception.Message -match 'EXE_PROCESS_PATH_MISMATCH_DO_NOT_KILL' }
if(-not $blocked -or $script:killed.Count -ne 0 -or $script:taskState -ne 'Running') {
    throw 'SIM_UNTRUSTED_PATH_DID_NOT_FAIL_BEFORE_STOP'
}
Write-Output 'SIM_WRONG_EXECUTABLE_PATH_FAIL_CLOSED_PASS'
Reset-Simulation
$script:replaceOnStop=$true
$blocked=$false
try { Stop-OnlyThisTask } catch { $blocked=$_.Exception.Message -match 'PROCESS_IDENTITY_CHANGED_ABORT_NO_KILL' }
if(-not $blocked -or $script:killed.Count -ne 0) {throw 'SIM_PID_REPLACEMENT_NOT_FAIL_CLOSED'}
Write-Output 'SIM_PID_SWAP_AFTER_TASK_STOP_FAIL_CLOSED_PASS'
exit 0
