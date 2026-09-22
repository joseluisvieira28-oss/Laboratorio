param(
    [Parameter(Mandatory=$true)]
    [string]$SourceRoot
)

$ErrorActionPreference = "Stop"
$RadarRoot = Split-Path -Parent $PSScriptRoot
$DataDir = Join-Path $RadarRoot "data"
New-Item -ItemType Directory -Force -Path $DataDir | Out-Null

$Required = @(
    "mexc_authenticated_preflight_receipt.json",
    "mexc_account_risk_state.json"
)

foreach ($name in $Required) {
    $src = Join-Path $SourceRoot $name
    if (-not (Test-Path $src)) {
        throw "Required sanitized MEXC receipt missing: $src"
    }

    # Parse before import. The Radar performs the authoritative schema,
    # freshness, provenance and secret checks; this protects against copying
    # truncated/non-JSON files into the live data directory.
    $null = Get-Content $src -Raw | ConvertFrom-Json

    $dst = Join-Path $DataDir $name
    $tmp = "$dst.tmp"
    Copy-Item $src $tmp -Force
    Move-Item $tmp $dst -Force

    $hash = (Get-FileHash $dst -Algorithm SHA256).Hash.ToLower()
    Write-Host "IMPORTED $name sha256=$hash"
}

Write-Host "PASS: sanitized MEXC receipts imported to $DataDir"
Write-Host "Radar will still FAIL_CLOSED if either receipt is stale, malformed, unsafe, or incompatible."
