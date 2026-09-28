$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $root "dist\OptionsV21ExecutionEconomicsAudit.exe"
$receiptRoot = Join-Path $root "live_receipts\options_v21_futures"
$out = Join-Path $receiptRoot "EXECUTION_ECONOMICS_TRUTH_GATE.json"

if (-not (Test-Path $exe)) { throw "Missing read-only audit executable: $exe" }
if (-not (Test-Path $receiptRoot)) {
    New-Item -ItemType Directory -Force -Path $receiptRoot | Out-Null
}

Write-Host ""
Write-Host "===== OPTIONS V2.1 EXECUTION ECONOMICS TRUTH GATE ====="
Write-Host "Receipt root : $receiptRoot"
Write-Host "Output       : $out"
Write-Host "Mode         : READ-ONLY ACCOUNT / LOCAL RECEIPTS ONLY"
Write-Host "Orders       : NONE"
Write-Host "API secrets  : NOT REQUIRED"
Write-Host "======================================================="

& $exe --receipt-root $receiptRoot --out $out
$code = $LASTEXITCODE

if (Test-Path $out) {
    Write-Host ""
    Get-Content -Raw $out | Write-Host
}
exit $code
