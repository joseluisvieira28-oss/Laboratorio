param(
    [string]$CsvPath = "$HOME\Downloads\DLS_RAW_VALIDATION_SAMPLE_V01.csv"
)

$ErrorActionPreference = "Stop"

Write-Host "DEFI-LIQUIDATION-SHOCK-001 - RAW VALIDATION SAMPLE V0.1"
Write-Host "READ-ONLY / SOURCE-ONLY / OUTCOME-BLIND"

$expectedSha = "B58AF58B0229969D38625CC2C4E138742477B1633D3FC06F3FA6B328064D5BDC"
$labDir = Split-Path -Parent $PSScriptRoot
Set-Location $labDir

if (-not (Test-Path $CsvPath)) {
    throw "Candidate CSV not found: $CsvPath"
}

$branch = git branch --show-current
if ($LASTEXITCODE -ne 0) { throw "git branch check failed" }
if ($branch.Trim() -ne "defi-liquidation-shock-v0.1") {
    throw "Wrong branch: $branch. Expected defi-liquidation-shock-v0.1"
}

$actualSha = (Get-FileHash $CsvPath -Algorithm SHA256).Hash.ToUpperInvariant()
if ($actualSha -ne $expectedSha) {
    throw "CSV SHA-256 mismatch. Expected $expectedSha but got $actualSha"
}
Write-Host "CSV SHA-256 verified: $actualSha"

if (-not $env:HELIUS_API_KEY -and -not $env:DLS_RPC_URL) {
    throw "HELIUS_API_KEY or DLS_RPC_URL is not set. Keep credentials local."
}

Write-Host "[1/4] Running network-free source collector tests..."
py .\source\test_source_collector_synthetic_v0_1.py
if ($LASTEXITCODE -ne 0) { throw "source collector synthetic tests failed" }

Write-Host "[2/4] Running network-free BigQuery verifier tests..."
py .\source\test_bigquery_verifier_synthetic_v0_1.py
if ($LASTEXITCODE -ne 0) { throw "BigQuery verifier synthetic tests failed" }

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$out = Join-Path $HOME "Desktop\DLS_RAW_SAMPLE_VERIFY_$stamp"

Write-Host "[3/4] Raw-verifying exactly the frozen sample through archival RPC..."
py .\source\verify_bigquery_candidates_v0_1.py --input $CsvPath --out-dir $out --max-unique-transactions 23
if ($LASTEXITCODE -ne 0) {
    Write-Host "Verifier failed closed. Preserve output directory and RUN_ERROR.json."
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
Write-Host "Upload the ZIP to this Crypto conversation or Drive. Share the ZIP/hash only - never the Helius key."
