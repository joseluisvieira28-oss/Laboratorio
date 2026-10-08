# Verify the complete flat Windows bundle without executing any EXE or secret.
param([string]$BundleRoot = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
$hashFile = Join-Path $BundleRoot 'SHA256SUMS.txt'
$buildFile = Join-Path $BundleRoot 'BUILD_INFO.json'
if (-not (Test-Path -LiteralPath $hashFile -PathType Leaf)) { throw 'MISSING_SHA256_MANIFEST' }
if (-not (Test-Path -LiteralPath $buildFile -PathType Leaf)) { throw 'MISSING_BUILD_INFO' }
$verified = @{}
foreach ($line in @(Get-Content -LiteralPath $hashFile -ErrorAction Stop)) {
    if ($line -notmatch '^(.+?)  ([a-fA-F0-9]{64})$') { throw 'INVALID_SHA256_MANIFEST_FORMAT' }
    $name = $Matches[1]
    $expected = $Matches[2].ToLowerInvariant()
    if ($name -ne [IO.Path]::GetFileName($name) -or $name -eq 'SHA256SUMS.txt') {
        throw 'INVALID_MANIFEST_FILE_NAME'
    }
    if ($verified.ContainsKey($name)) { throw 'DUPLICATE_MANIFEST_ENTRY' }
    $file = Join-Path $BundleRoot $name
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw 'MISSING_MANIFEST_FILE' }
    $actual = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw 'HASH_MISMATCH' }
    $verified[$name] = $true
}
$essential = @(
    'MEXCTripleFishingOperatorV03.exe',
    'MEXCTripleFishingReadyV03.exe',
    'BuildOptionsCorrectionOverlayV01.exe',
    'Run_MEXC_Triple_Fishing_V03.ps1',
    'OPTIONS_V21_HISTORICAL_FEE_CORRECTION_CATALOG_V01.json',
    'BUILD_INFO.json',
    'Inspect_MEXC_Triple_Fishing_V03_READONLY.ps1'
)
foreach ($name in $essential) {
    if (-not $verified.ContainsKey($name)) { throw 'MISSING_REQUIRED_MANIFEST_ENTRY' }
}
$info = Get-Content -LiteralPath $buildFile -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
if ($info.build -ne 'TRIPLE_FISHING_OPERATOR_V0.3' -or
    [string]$info.source_sha -notmatch '^[a-fA-F0-9]{40}$' -or
    $info.live_armed_by_build -ne $false -or
    $info.exchange_contacted_by_build -ne $false -or
    $info.order_created_by_build -ne $false -or
    $info.main_merged -ne $false) {
    throw 'BUILD_INFO_AUTHORITY_NOT_VERIFIED'
}
[pscustomobject]@{
    Verdict = 'BUNDLE_HASHES_PASS'
    FileCount = $verified.Count
    SourceSha = $info.source_sha
    BuildBranch = $info.branch
    AccountPositionsVerified = 'NOT_CHECKED'
    TradingAuthorized = $false
}
