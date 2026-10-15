# Simulated observer lifecycle. Command mocks guarantee no real Task Scheduler or PID mutation.
$ErrorActionPreference='Stop'
$source=Join-Path (Split-Path -Parent $PSScriptRoot) 'engine/convex_ten_governance/ATUALIZAR_UMA_CANA_READONLY.ps1'
$errors=$null;$tokens=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($source,[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'CUTOVER_PARSER_FAILED'}
$names=@('Get-VersionProcesses','Get-VersionProcessCount','Assert-VerifiedProcesses','ProcessFingerprint','Wait-Exit','Stop-OnlyThisTask')
$defs=@($ast.FindAll({param($x) $x -is [Management.Automation.Language.FunctionDefinitionAst]},$true))
foreach($name in $names){
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
$script:childDiesWithParent=$false
$script:recyclePidOnLookup=$false
function Get-CimInstance {
    [CmdletBinding()]
    param([string]$ClassName,[string]$Filter)
    if($Filter -match '^ProcessId=([0-9]+)$'){
        $wantedId=[int]$Matches[1]
        if($script:recyclePidOnLookup -and $wantedId -eq 1201){
            $script:simProcs[0]=[pscustomobject]@{ProcessId=1201;ExecutablePath=$expected;CreationDate=[datetime]'2026-10-15T12:59:59Z'}
        }
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
    if($script:replaceOnStop){
        $script:simProcs=@(
          [pscustomobject]@{ProcessId=1201;ExecutablePath=$expected;CreationDate=[datetime]'2026-10-15T12:00:00Z'},
          [pscustomobject]@{ProcessId=1303;ExecutablePath=$expected;CreationDate=[datetime]'2026-10-15T12:00:05Z'}
        )
    }
}
function Stop-Process {
    [CmdletBinding()]
    param([int]$Id,[switch]$Force)
    $script:killed+=$Id
    $script:simProcs=@($script:simProcs|Where-Object{
      $_.ProcessId -ne $Id -and -not ($script:childDiesWithParent -and $Id -eq 1201 -and $_.ProcessId -eq 1202)
    })
}
function Start-Sleep {
    [CmdletBinding()]
    param([int]$Seconds)
}
function Reset-Simulation {
    $script:taskState='Running'
    $script:killed=@()
    $script:replaceOnStop=$false
    $script:childDiesWithParent=$false
    $script:recyclePidOnLookup=$false
    $script:simProcs=@(
      [pscustomobject]@{ProcessId=1201;ExecutablePath=$expected;CreationDate=[datetime]'2026-10-15T12:00:00Z'},
      [pscustomobject]@{ProcessId=1202;ExecutablePath=$expected;CreationDate=[datetime]'2026-10-15T12:00:05Z'}
    )
}
Reset-Simulation
Stop-OnlyThisTask
if($script:taskState -ne 'Ready' -or $script:simProcs.Count -ne 0 -or ($script:killed -join ',') -ne '1201,1202'){
    throw 'SIM_ORPHAN_RECOVERY_DID_NOT_STOP_EXPECTED_TWO'
}
Write-Output 'SIM_VERIFIED_ORPHAN_REAP_PASS'
Reset-Simulation
$script:simProcs[1].ExecutablePath='C:\Different\UNTRUSTED.exe'
$blocked=$false
try{Stop-OnlyThisTask}catch{$blocked=$_.Exception.Message -match 'EXE_PROCESS_PATH_MISMATCH_DO_NOT_KILL'}
if(-not $blocked -or $script:killed.Count -ne 0 -or $script:taskState -ne 'Running'){
    throw 'SIM_UNTRUSTED_PATH_NOT_FAIL_CLOSED'
}
Write-Output 'SIM_WRONG_PATH_FAIL_CLOSED_PASS'
Reset-Simulation
$script:replaceOnStop=$true
$blocked=$false
try{Stop-OnlyThisTask}catch{$blocked=$_.Exception.Message -match 'PROCESS_IDENTITY_CHANGED_ABORT_NO_KILL'}
if(-not $blocked -or $script:killed.Count -ne 0){throw 'SIM_PID_SWAPPED_NOT_FAIL_CLOSED'}
Write-Output 'SIM_PID_CHANGED_FAIL_CLOSED_PASS'
Reset-Simulation
$script:childDiesWithParent=$true
Stop-OnlyThisTask
if($script:simProcs.Count -ne 0 -or ($script:killed -join ',') -ne '1201'){
    throw 'SIM_AUTO_EXIT_CHILD_NOT_HANDLED'
}
Write-Output 'SIM_CHILD_AUTO_EXIT_PASS'
Reset-Simulation
$script:recyclePidOnLookup=$true
$blocked=$false
try{Stop-OnlyThisTask}catch{$blocked=$_.Exception.Message -match 'PID_REUSED_ABORT_NO_KILL'}
if(-not $blocked -or $script:killed.Count -ne 0){throw 'SIM_PID_REUSE_NOT_FAIL_CLOSED'}
Write-Output 'SIM_PID_REUSE_FAIL_CLOSED_PASS'
exit 0
