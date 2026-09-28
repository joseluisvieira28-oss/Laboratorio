param(
    [string]$ReceiptRoot
)

$ErrorActionPreference = "Stop"

$bundleRoot = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $bundleRoot "dist\OptionsV21ExecutionEconomicsAudit.exe"
$taskName = "CryptoLab-OPTIONS-V21-Futures-AutoLive"

if (-not (Test-Path $exe)) { throw "Missing read-only audit executable: $exe" }

$source = "EXPLICIT_ARGUMENT"
if ([string]::IsNullOrWhiteSpace($ReceiptRoot)) {
    $source = "SCHEDULED_TASK"
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task -and $task.Actions -and $task.Actions.Count -gt 0) {
        $args = [string]$task.Actions[0].Arguments
        $match = [regex]::Match($args, '-File\s+"([^"]+)"', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
        if ($match.Success) {
            $runner = $match.Groups[1].Value
            if (Test-Path $runner) {
                $installedWindows = Split-Path -Parent $runner
                $installedRoot = Split-Path -Parent $installedWindows
                $candidate = Join-Path $installedRoot "live_receipts\options_v21_futures"
                if (Test-Path $candidate) {
                    $ReceiptRoot = $candidate
                }
            }
        }
    }
}

if ([string]::IsNullOrWhiteSpace($ReceiptRoot)) {
    $source = "BUNDLE_LOCAL_FALLBACK"
    $ReceiptRoot = Join-Path $bundleRoot "live_receipts\options_v21_futures"
}

if (-not (Test-Path $ReceiptRoot)) {
    throw "Receipt root not found: $ReceiptRoot. Pass -ReceiptRoot <path> explicitly if the scheduled-task installation cannot be resolved."
}

$out = Join-Path $ReceiptRoot "EXECUTION_ECONOMICS_TRUTH_GATE.json"

Write-Host ""
Write-Host "===== OPTIONS V2.1 EXECUTION ECONOMICS TRUTH GATE ====="
Write-Host "Receipt source: $source"
Write-Host "Receipt root  : $ReceiptRoot"
Write-Host "Output        : $out"
Write-Host "Mode          : LOCAL RECEIPTS / NO EXCHANGE MUTATION"
Write-Host "API secrets   : NOT REQUIRED"
Write-Host "Task restart  : NONE"
Write-Host "Orders        : NONE"
Write-Host "======================================================="

& $exe --receipt-root $ReceiptRoot --out $out
$code = $LASTEXITCODE

if (Test-Path $out) {
    Write-Host ""
    Get-Content -Raw $out | Write-Host
}
exit $code
