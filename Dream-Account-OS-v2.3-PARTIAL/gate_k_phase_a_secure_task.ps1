param(
    [Parameter(Mandatory=$true)][ValidateSet('MORNING','MIDDAY','EVENING')][string]$Window,
    [int]$Cycles = 5,
    [int]$IntervalSeconds = 900
)

$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$EvidenceDir = Join-Path $Root 'gate_k_phase_a_evidence'
$SecretDir = Join-Path $EvidenceDir 'secure'
$LogDir = Join-Path $EvidenceDir 'scheduler_logs'
$AccessFile = Join-Path $SecretDir 'mexc_readonly_access.dpapi'
$SecretFile = Join-Path $SecretDir 'mexc_readonly_secret.dpapi'
$Batch = Join-Path $Root 'run_gate_k_phase_a_campaign_windows.bat'
$Summary = Join-Path $Root 'show_gate_k_phase_a_summary_windows.bat'

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Log = Join-Path $LogDir ("{0}_{1}.log" -f $Stamp, $Window.ToLowerInvariant())

function Fail-Closed([string]$Message) {
    Add-Content -Path $Log -Value ("[{0}] BLOCKED: {1}" -f (Get-Date -Format o), $Message)
    Write-Error $Message
    exit 1
}

if (-not (Test-Path -LiteralPath $AccessFile)) { Fail-Closed 'Encrypted read-only access key file is missing.' }
if (-not (Test-Path -LiteralPath $SecretFile)) { Fail-Closed 'Encrypted read-only secret key file is missing.' }
if (-not (Test-Path -LiteralPath $Batch)) { Fail-Closed 'Controlled batch launcher is missing.' }
if ($Cycles -lt 1 -or $Cycles -gt 20) { Fail-Closed 'Cycles must be between 1 and 20.' }
if ($IntervalSeconds -lt 120 -or $IntervalSeconds -gt 21600) { Fail-Closed 'IntervalSeconds must be between 120 and 21600.' }

try {
    $AccessSecure = Get-Content -LiteralPath $AccessFile -Raw | ConvertTo-SecureString
    $SecretSecure = Get-Content -LiteralPath $SecretFile -Raw | ConvertTo-SecureString
    $AccessPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($AccessSecure)
    $SecretPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecretSecure)
    try {
        $env:MEXC_READONLY_ACCESS_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($AccessPtr)
        $env:MEXC_READONLY_SECRET_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($SecretPtr)
    }
    finally {
        if ($AccessPtr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($AccessPtr) }
        if ($SecretPtr -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($SecretPtr) }
    }

    $env:MEXC_READONLY_SCOPE_ATTESTED = '1'
    $env:MEXC_READONLY_RECONCILE_ENABLE = '1'
    $env:MEXC_SHADOW_REHEARSAL_ENABLE = '1'

    Add-Content -Path $Log -Value ("[{0}] START window={1} cycles={2} interval={3}s" -f (Get-Date -Format o), $Window, $Cycles, $IntervalSeconds)
    Push-Location $Root
    try {
        & cmd.exe /d /c ('"{0}" {1} {2}' -f $Batch, $Cycles, $IntervalSeconds).Replace('\"','"') 2>&1 | Tee-Object -FilePath $Log -Append
        $ExitCode = $LASTEXITCODE
        if (Test-Path -LiteralPath $Summary) {
            Add-Content -Path $Log -Value "`r`n--- OPERATIONAL SUMMARY ---"
            & cmd.exe /d /c ('"{0}"' -f $Summary).Replace('\"','"') 2>&1 | Tee-Object -FilePath $Log -Append
        }
    }
    finally {
        Pop-Location
    }

    if ($ExitCode -ne 0) { Fail-Closed ("Controlled batch returned exit code {0}. No retry attempted." -f $ExitCode) }
    Add-Content -Path $Log -Value ("[{0}] PASS window={1}" -f (Get-Date -Format o), $Window)
    exit 0
}
catch {
    Fail-Closed $_.Exception.Message
}
finally {
    Remove-Item Env:MEXC_READONLY_ACCESS_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_READONLY_SECRET_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_READONLY_SCOPE_ATTESTED -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_READONLY_RECONCILE_ENABLE -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_SHADOW_REHEARSAL_ENABLE -ErrorAction SilentlyContinue
}
