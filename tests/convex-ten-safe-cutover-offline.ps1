# Offline-only static assurance for scripts; never touches scheduled tasks or any secrets.
$ErrorActionPreference='Stop'
$root=Join-Path (Split-Path -Parent $PSScriptRoot) 'engine/convex_ten_governance'
$names=@('ATUALIZAR_UMA_CANA_READONLY.ps1','ESTADO_10_CANAS_READONLY.ps1','RECUPERAR_UMA_CANA_READONLY.ps1')
foreach($name in $names) {
    $path=Join-Path $root $name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {throw "FILE_MISSING:$name"}
    $tokens=$null;$errors=$null
    $ast=[Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors)
    if ($errors.Count -gt 0) {
        throw ("PS_PARSE_FAILED:"+$name+":"+(($errors|ForEach-Object{$_.Message}) -join ';'))
    }
    Write-Output ("PS_PARSER_PASS: "+$name)
}
$up=Get-Content -LiteralPath (Join-Path $root 'ATUALIZAR_UMA_CANA_READONLY.ps1') -Raw
foreach($token in @(
    'CONFIRMO_10_CANAS_READONLY',
    'PREFLIGHT_PASS_NO_CHANGES',
    'Wait-Exit',
    'INSTALLED_HASH_MISMATCH',
    'Stop-ScheduledTask -TaskName $taskName',
    'Start-ScheduledTask -TaskName $taskName',
    'ORIGINAL_EXE_RESTART_REQUESTED_CURRENT_OUTBOX_PRESERVED',
    'SOURCE_EXE_NOT_AUDITED_V2',
    'V12_EXE_NOT_AUDITED_PR239',
    'matches'
)) {
    if ($token -eq 'matches') {continue}
    if (-not $up.Contains($token)) {throw "INVARIANT_MISSING:$token"}
}
# Failure-mode regressions: stop exit-timeout must not strand V07 silently,
# incomplete binary copy must enter rollback, and no twin EXEs on restart.
if (-not $up.Contains('CHILD_EXE_STILL_PRESENT_NO_RESTART_TO_AVOID_TWIN_OBSERVERS')) {
    throw 'MISSING_FAIL_CLOSED_TWIN_PROCESS_GUARD'
}
if (-not ($up -match '(?s)\$taskWasStopped=\$true\s+Stop-OnlyThisTask')) {
    throw 'STOP_TRACKING_MUST_BE_SET_BEFORE_POSSIBLE_WAIT_EXIT_FAILURE'
}
if (-not ($up -match '(?s)\$binarySwapped=\$true\s+Copy-Item -LiteralPath \$source')) {
    throw 'PARTIAL_BINARY_COPY_MUST_TRIGGER_ROLLBACK'
}
if ($up -match 'Invoke-RestMethod|Invoke-WebRequest|api\.telegram\.org|api\.mexc\.com|/order/submit') {
    throw 'UPDATER_MUST_NOT_MAKE_EXTERNAL_REQUESTS'
}
$probe=Get-Content -LiteralPath (Join-Path $root 'ESTADO_10_CANAS_READONLY.ps1') -Raw
if ($probe -match '(?i)Stop-ScheduledTask|Start-ScheduledTask|Disable-ScheduledTask|Send-Telegram|Invoke-RestMethod') {
    throw 'READONLY_HEALTH_RECEIPT_HAS_MUTATION'
}
# Negative package receipt: missing installer files must cause fail-closed before
# any Get-ScheduledTask, copying, stopping or starting. No real machine touched.
$temp=Join-Path ([IO.Path]::GetTempPath()) ('convex10_negative_'+[Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temp -Force | Out-Null
$priorLocalAppData=$env:LOCALAPPDATA
$env:LOCALAPPDATA=$temp
try {
    foreach($v in @('V07','V11','V12')) {
        $out=& pwsh -NoProfile -File (Join-Path $root 'ATUALIZAR_UMA_CANA_READONLY.ps1') -Version $v -PackageDir $temp -Mode Preflight 2>&1 | Out-String
        if ($LASTEXITCODE -eq 0 -or $out -notmatch 'SOURCE_EXE_NOT_FOUND') {
            throw "NEGATIVE_PACKAGE_DID_NOT_FAIL_CLOSED:$v"
        }
    }
    Write-Output 'OFFLINE_MISSING_ARTIFACT_NEGATIVE_GATE_PASS'
} finally {
    $env:LOCALAPPDATA=$priorLocalAppData
    Remove-Item -LiteralPath $temp -Recurse -Force
}
Write-Output 'CONVEX10_UPGRADE_SCRIPTS_OFFLINE_PASS_NO_TASK_CHANGES'
exit 0
