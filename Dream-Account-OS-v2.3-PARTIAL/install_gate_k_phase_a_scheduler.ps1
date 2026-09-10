param(
    [ValidatePattern('^([01]\d|2[0-3]):[0-5]\d$')][string]$MorningTime = '07:30',
    [ValidatePattern('^([01]\d|2[0-3]):[0-5]\d$')][string]$MiddayTime = '13:00',
    [ValidatePattern('^([01]\d|2[0-3]):[0-5]\d$')][string]$EveningTime = '19:30',
    [ValidateRange(1,20)][int]$Cycles = 5,
    [ValidateRange(120,21600)][int]$IntervalSeconds = 900
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$EvidenceDir = Join-Path $Root 'gate_k_phase_a_evidence'
$SecretDir = Join-Path $EvidenceDir 'secure'
$Runner = Join-Path $Root 'gate_k_phase_a_secure_task.ps1'

if (-not (Test-Path -LiteralPath $Runner)) { throw 'Secure scheduled-task runner is missing.' }

$required = @(
    'MEXC_READONLY_ACCESS_KEY',
    'MEXC_READONLY_SECRET_KEY',
    'MEXC_READONLY_SCOPE_ATTESTED',
    'MEXC_READONLY_RECONCILE_ENABLE',
    'MEXC_SHADOW_REHEARSAL_ENABLE'
)
foreach ($name in $required) {
    $value = [Environment]::GetEnvironmentVariable($name, 'Process')
    if ([string]::IsNullOrWhiteSpace($value)) { throw "$name is missing from the current PowerShell session." }
}
foreach ($flag in @('MEXC_READONLY_SCOPE_ATTESTED','MEXC_READONLY_RECONCILE_ENABLE','MEXC_SHADOW_REHEARSAL_ENABLE')) {
    if ([Environment]::GetEnvironmentVariable($flag, 'Process') -ne '1') { throw "$flag must equal 1." }
}

New-Item -ItemType Directory -Force -Path $SecretDir | Out-Null
$accessPath = Join-Path $SecretDir 'mexc_readonly_access.dpapi'
$secretPath = Join-Path $SecretDir 'mexc_readonly_secret.dpapi'

$accessSecure = ConvertTo-SecureString $env:MEXC_READONLY_ACCESS_KEY -AsPlainText -Force
$secretSecure = ConvertTo-SecureString $env:MEXC_READONLY_SECRET_KEY -AsPlainText -Force
$accessSecure | ConvertFrom-SecureString | Set-Content -LiteralPath $accessPath -Encoding UTF8 -NoNewline
$secretSecure | ConvertFrom-SecureString | Set-Content -LiteralPath $secretPath -Encoding UTF8 -NoNewline

try {
    & icacls.exe $SecretDir /inheritance:r /grant:r "${env:USERNAME}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "icacls returned exit code $LASTEXITCODE" }
} catch {
    throw "Could not harden scheduler credential directory ACLs: $($_.Exception.Message)"
}

$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 3)
$settings.WakeToRun = $true

$windows = @(
    @{ Name='MORNING'; Time=$MorningTime },
    @{ Name='MIDDAY'; Time=$MiddayTime },
    @{ Name='EVENING'; Time=$EveningTime }
)

foreach ($window in $windows) {
    $taskName = "DreamAccountOS-GateK-PhaseA-$($window.Name)"
    $todayAt = [DateTime]::Today.Add([TimeSpan]::Parse($window.Time))
    $trigger = New-ScheduledTaskTrigger -Daily -At $todayAt
    $arguments = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "{0}" -Window {1} -Cycles {2} -IntervalSeconds {3}' -f $Runner, $window.Name, $Cycles, $IntervalSeconds
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $arguments -WorkingDirectory $Root
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Gate K Phase A SHADOW / READ-ONLY observation window. No exchange mutation or live trading.' -Force | Out-Null
}

Write-Host 'Gate K Phase A automated scheduler installed.'
Write-Host "Morning: $MorningTime"
Write-Host "Midday: $MiddayTime"
Write-Host "Evening: $EveningTime"
Write-Host "Each window: $Cycles cycles, $IntervalSeconds seconds apart"
Write-Host 'Credentials: Windows DPAPI CurrentUser ciphertext; plaintext is not written to disk.'
Write-Host 'Task logon mode: current user Interactive; stay signed in (screen may be locked).'
Write-Host 'WakeToRun requested; actual wake behavior depends on Windows power policy/hardware.'
Write-Host 'No missed-window retry loop is configured. Each task invokes one controlled batch only.'
