param(
    [ValidateSet('SEMANTIC','COVERAGE','ALL')]
    [string]$Stage = 'ALL',
    [string]$WorkDir = ''
)

$ErrorActionPreference = 'Stop'

Write-Host '============================================================'
Write-Host 'CROSS-VENUE FUNDING/BASIS - HYPERLIQUID ASSET_CTX V0.4.4'
Write-Host 'PROVENANCE ONLY - REQUESTER PAYS - NO ECONOMIC OUTPUTS'
Write-Host '============================================================'
Write-Host "Stage: $Stage"
Write-Host '2026: FORBIDDEN'
Write-Host 'MEXC: FORBIDDEN'
Write-Host 'Carry/PnL/basis return/signals: FORBIDDEN'
Write-Host ''

$AppRoot = Split-Path -Parent $PSScriptRoot
$Probe = Join-Path $AppRoot 'research\cross_venue_funding_basis_hl_asset_ctx_v044.py'
$Authority = Join-Path $AppRoot 'research\CROSS_VENUE_FUNDING_BASIS_HL_ASSET_CTX_PROVENANCE_V044.json'
$Ledger = Join-Path $AppRoot 'research\CROSS_VENUE_FUNDING_BASIS_DATASET_EXPOSURE_LEDGER_V01.json'

foreach ($P in @($Probe,$Authority,$Ledger)) {
    if (-not (Test-Path -LiteralPath $P)) { throw "FAIL-CLOSED: missing required file: $P" }
}

if (-not $WorkDir) { $WorkDir = Join-Path $AppRoot 'v044_asset_ctx_work' }
$RawDir = Join-Path $WorkDir 'raw_transient'
$DailyDir = Join-Path $WorkDir 'daily_receipts'
$FinalDir = Join-Path $WorkDir 'final_receipts'
New-Item -ItemType Directory -Force -Path $RawDir,$DailyDir,$FinalDir | Out-Null

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) { throw 'FAIL-CLOSED: AWS CLI not found.' }

$PythonExe = $null
$PythonPrefix = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonExe = 'py'; $PythonPrefix = @('-3')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonExe = 'python'; $PythonPrefix = @()
} else {
    throw 'FAIL-CLOSED: Python 3 not found.'
}

& $PythonExe @PythonPrefix -c 'import lz4.frame' 2>$null
if ($LASTEXITCODE -ne 0) { throw 'FAIL-CLOSED: Python package lz4 missing. Run: py -3 -m pip install lz4' }

# Harmless read-only credential check. No bucket listing is performed.
& aws sts get-caller-identity --output json | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'FAIL-CLOSED: AWS identity check failed.' }
Write-Host 'Local prerequisites + AWS identity: PASS'

function Invoke-DayProbe {
    param([datetime]$Date)
    $Iso = $Date.ToString('yyyy-MM-dd')
    if ($Date.Year -eq 2026 -or $Date -lt [datetime]'2023-09-01' -or $Date -gt [datetime]'2025-12-31') {
        throw "FAIL-CLOSED: date outside frozen range: $Iso"
    }
    $Stamp = $Date.ToString('yyyyMMdd')
    $Receipt = Join-Path $DailyDir ("asset_ctx_" + $Stamp + '.json')
    if (Test-Path -LiteralPath $Receipt) {
        Write-Host "$Iso receipt already exists - reusing provenance receipt."
        return
    }
    $Raw = Join-Path $RawDir ("asset_ctxs_" + $Stamp + '.csv.lz4')
    if (Test-Path -LiteralPath $Raw) { Remove-Item -Force -LiteralPath $Raw }
    $Key = "asset_ctxs/$Stamp.csv.lz4"
    Write-Host "GET s3://hyperliquid-archive/$Key"
    & aws s3api get-object --bucket hyperliquid-archive --key $Key --request-payer requester $Raw | Out-Null
    $AwsExit = $LASTEXITCODE
    if ($AwsExit -ne 0 -or -not (Test-Path -LiteralPath $Raw)) {
        if (Test-Path -LiteralPath $Raw) { Remove-Item -Force -LiteralPath $Raw }
        & $PythonExe @PythonPrefix $Probe missing-day --date $Iso --reason 'AWS_GET_FAILED_OR_OBJECT_UNAVAILABLE' --out $Receipt
        if ($LASTEXITCODE -ne 0) { throw "FAIL-CLOSED: unable to write missing-day receipt for $Iso" }
        Write-Warning "$Iso unavailable; fail-closed daily receipt recorded."
        return
    }
    try {
        & $PythonExe @PythonPrefix $Probe inspect-day --file $Raw --date $Iso --out $Receipt
        if ($LASTEXITCODE -ne 0) { throw "Day parser failed closed for $Iso" }
    } finally {
        Remove-Item -Force -LiteralPath $Raw -ErrorAction SilentlyContinue
    }
}

function Get-SemanticDates {
    $Dates = @()
    $d = [datetime]'2023-09-01'
    while ($d -le [datetime]'2023-09-07') { $Dates += $d; $d = $d.AddDays(1) }
    $d = [datetime]'2023-12-01'
    while ($d -le [datetime]'2023-12-22') { $Dates += $d; $d = $d.AddDays(1) }
    return $Dates
}

function Run-Semantics {
    Write-Host ''
    Write-Host '=== STAGE A - OFFICIAL ARCHIVE SEMANTIC IDENTIFICATION ==='
    Write-Host 'Authorized requester-pays GETs: fixed 29 dates, except receipts already present.'
    foreach ($d in (Get-SemanticDates)) { Invoke-DayProbe -Date $d }
    $Out = Join-Path $FinalDir 'CROSS_VENUE_FUNDING_BASIS_V044_STAGE_A_SEMANTICS_RECEIPT.json'
    & $PythonExe @PythonPrefix $Probe aggregate-semantics --receipt-dir $DailyDir --out $Out
    $Code = $LASTEXITCODE
    Write-Host "Stage A receipt: $Out"
    if ($Code -ne 0) {
        Write-Host 'FINAL STAGE A GATE: FAIL-CLOSED'
        Write-Host 'Do NOT run coverage. Do NOT alter formula, assets, dates, tolerance or thresholds.'
        return $false
    }
    Write-Host 'FINAL STAGE A GATE: PASS'
    return $true
}

function Seed-PriorPartialDay {
    $Receipt = Join-Path $DailyDir 'asset_ctx_20240901.json'
    if (-not (Test-Path -LiteralPath $Receipt)) {
        & $PythonExe @PythonPrefix $Probe seed-prior-20240901 --out $Receipt
        if ($LASTEXITCODE -ne 0) { throw 'FAIL-CLOSED: unable to seed prior 2024-09-01 provenance.' }
        Write-Host 'Seeded prior authorized 2024-09-01 partial-day provenance; no duplicate AWS GET.'
    }
}

function Run-Coverage {
    Write-Host ''
    Write-Host '=== STAGE B - FULL CALENDAR COVERAGE SWEEP ==='
    Write-Host 'Range: 2023-09-01 through 2025-12-31 inclusive'
    Write-Host 'Selection uses timestamps/availability only. Economic outputs remain forbidden.'
    Seed-PriorPartialDay
    $d = [datetime]'2023-09-01'
    $end = [datetime]'2025-12-31'
    while ($d -le $end) {
        Invoke-DayProbe -Date $d
        $d = $d.AddDays(1)
    }
    $Out = Join-Path $FinalDir 'CROSS_VENUE_FUNDING_BASIS_V044_STAGE_B_COVERAGE_RECEIPT.json'
    & $PythonExe @PythonPrefix $Probe aggregate-coverage --receipt-dir $DailyDir --out $Out
    $Code = $LASTEXITCODE
    Write-Host "Stage B receipt: $Out"
    if ($Code -ne 0) {
        Write-Host 'FINAL STAGE B GATE: FAIL-CLOSED - ZERO COMMON COMPLETE MONTHS'
        return $false
    }
    Write-Host 'FINAL STAGE B GATE: PASS - COMMON COMPLETE MONTHS EXIST'
    return $true
}

if ($Stage -eq 'SEMANTIC') {
    if (-not (Run-Semantics)) { exit 2 }
    exit 0
}

if ($Stage -eq 'COVERAGE') {
    $SemanticReceipt = Join-Path $FinalDir 'CROSS_VENUE_FUNDING_BASIS_V044_STAGE_A_SEMANTICS_RECEIPT.json'
    if (-not (Test-Path -LiteralPath $SemanticReceipt)) { throw 'FAIL-CLOSED: Stage A PASS receipt required before COVERAGE.' }
    $S = Get-Content -LiteralPath $SemanticReceipt -Raw | ConvertFrom-Json
    if ($S.semantic_probe_pass -ne $true) { throw 'FAIL-CLOSED: Stage A semantic gate is not PASS.' }
    if (-not (Run-Coverage)) { exit 3 }
    exit 0
}

if ($Stage -eq 'ALL') {
    if (-not (Run-Semantics)) { exit 2 }
    if (-not (Run-Coverage)) { exit 3 }
    Write-Host ''
    Write-Host '============================================================'
    Write-Host 'V0.4.4 PROVENANCE COMPLETE'
    Write-Host 'Discovery remains BLOCKED pending calendar materialization + economic freeze.'
    Write-Host 'No carry/PnL/basis-return result was computed.'
    Write-Host '============================================================'
    exit 0
}
