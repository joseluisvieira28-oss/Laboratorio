param(
    [Parameter(Mandatory=$true)]
    [string]$CsvPath
)

$ErrorActionPreference = "Stop"

Write-Host "DEFI-LIQUIDATION-SHOCK-001 — PC RAW VERIFY V0.1"
Write-Host "READ-ONLY / SOURCE-ONLY / OUTCOME-BLIND"

$labDir = Split-Path -Parent $PSScriptRoot
Set-Location $labDir

if (-not (Test-Path $CsvPath)) {
    throw "Candidate CSV not found: $CsvPath"
}

$branch = git branch --show-current
if ($LASTEXITCODE -ne 0) {
    throw "git branch check failed"
}
if ($branch.Trim() -ne "defi-liquidation-shock-v0.1") {
    throw "Wrong branch: $branch. Expected defi-liquidation-shock-v0.1"
}

if (-not $env:HELIUS_API_KEY -and -not $env:DLS_RPC_URL) {
    throw "Set HELIUS_API_KEY locally (or DLS_RPC_URL) before running. Do not paste the secret into chat or GitHub."
}

Write-Host "[1/4] Running network-free source collector tests..."
py .\source\test_source_collector_synthetic_v0_1.py
if ($LASTEXITCODE -ne 0) { throw "source collector synthetic tests failed" }

Write-Host "[2/4] Running network-free BigQuery verifier tests..."
py .\source\test_bigquery_verifier_synthetic_v0_1.py
if ($LASTEXITCODE -ne 0) { throw "BigQuery verifier synthetic tests failed" }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $HOME "Desktop\DLS_VERIFY_2021_2024_$stamp"

Write-Host "[3/4] Raw-verifying BigQuery candidates through archival RPC..."
py .\source\verify_bigquery_candidates_v0_1.py --input $CsvPath --out-dir $out
if ($LASTEXITCODE -ne 0) {
    Write-Host "Verifier failed closed. Preserve the output directory and RUN_ERROR.json."
    exit $LASTEXITCODE
}

Write-Host "[4/4] Packaging evidence and calculating SHA-256..."
$zip = "$out.zip"
Compress-Archive -Path "$out\*" -DestinationPath $zip -CompressionLevel Optimal
$hash = Get-FileHash $zip -Algorithm SHA256

Write-Host ""
Write-Host "COMPLETE"
Write-Host "Evidence folder: $out"
Write-Host "Evidence ZIP:    $zip"
Write-Host "SHA-256:         $($hash.Hash)"
Write-Host ""
Write-Host "Upload the ZIP to Drive or the Crypto conversation. Share the filename and SHA-256 only — never the Helius key."
