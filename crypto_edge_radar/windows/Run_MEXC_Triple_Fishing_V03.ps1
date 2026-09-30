param([string]$BundleRoot = $PSScriptRoot)

$ErrorActionPreference = "Stop"

$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV03"
$receiptRoot = Join-Path $runtime "live_receipts\operator_futures_v03"
$stateDir = Join-Path $runtime "live_state"
$dataDir = Join-Path $runtime "data"
$archiveRoot = Join-Path $runtime "historical_options_receipts"
$overlay = Join-Path $stateDir "OPTIONS_V21_PNL_CORRECTION_OVERLAY_V01.json"
$armed = Join-Path $runtime "OPERATOR_FUTURES_V03_ARMED.json"
$kill = Join-Path $runtime "OPERATOR_FUTURES_V03_KILL_SWITCH"
$slot = Join-Path $stateDir "GLOBAL_POSITION_SLOT_V03.json"

$mainExe = Join-Path $BundleRoot "MEXCTripleFishingOperatorV03.exe"
$overlayExe = Join-Path $BundleRoot "BuildOptionsCorrectionOverlayV01.exe"
$catalog = Join-Path $BundleRoot "OPTIONS_V21_HISTORICAL_FEE_CORRECTION_CATALOG_V01.json"

New-Item -ItemType Directory -Force -Path $runtime,$receiptRoot,$stateDir,$dataDir | Out-Null
foreach ($p in @($mainExe,$overlayExe,$catalog,$archiveRoot)) {
    if (-not (Test-Path -LiteralPath $p)) { throw "Required triple-fishing path missing: $p" }
}

& $overlayExe --catalog $catalog --receipt-root $archiveRoot --out $overlay
if ($LASTEXITCODE -ne 0) { throw "OPTIONS correction overlay build failed closed." }

$secretDir = Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
$keyPath = Join-Path $secretDir "mexc_api_key.dpapi"
$secretPath = Join-Path $secretDir "mexc_api_secret.dpapi"

function Unprotect-LocalSecret {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Missing local DPAPI secret: $Path" }
    $cipher = Get-Content -Raw -LiteralPath $Path
    $secure = ConvertTo-SecureString $cipher
    $cred = New-Object System.Management.Automation.PSCredential("local", $secure)
    return $cred.GetNetworkCredential().Password
}

$apiKey = $null
$apiSecret = $null
try {
    $apiKey = Unprotect-LocalSecret $keyPath
    $apiSecret = Unprotect-LocalSecret $secretPath
    $env:MEXC_API_KEY = $apiKey
    $env:MEXC_API_SECRET = $apiSecret
    $env:CRYPTO_LAB_PNL_CORRECTION_OVERLAY = $overlay

    $roots = @($archiveRoot)
    $legacyBnbReceipts = Join-Path $env:LOCALAPPDATA "CryptoLab\OperatorFuturesV02\live_receipts"
    if (Test-Path -LiteralPath $legacyBnbReceipts) { $roots += $legacyBnbReceipts }
    $env:CRYPTO_LAB_EXTERNAL_RECEIPT_ROOTS = ($roots -join [IO.Path]::PathSeparator)

    $mainArgs = @(
        "--receipt-root",$receiptRoot,
        "--armed-path",$armed,
        "--kill-switch",$kill,
        "--status-path",(Join-Path $stateDir "operator_futures_engine_v03.json"),
        "--global-slot-path",$slot,
        "--supervisor-state",(Join-Path $stateDir "triple_fishing_operator_v03.json"),
        "--bnb-state",(Join-Path $stateDir "bnb_operator_source_v03.json"),
        "--options-db",(Join-Path $dataDir "options_v21_operator.sqlite3"),
        "--options-state",(Join-Path $stateDir "options_v21_operator_source_v03.json"),
        "--dh03-market-db",(Join-Path $dataDir "dh03_market.sqlite3"),
        "--dh03-evidence-db",(Join-Path $dataDir "dh03_evidence.sqlite3"),
        "--dh03-state",(Join-Path $stateDir "dh03_operator_source_v03.json")
    )
    & $mainExe @mainArgs
    exit $LASTEXITCODE
}
finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:CRYPTO_LAB_PNL_CORRECTION_OVERLAY -ErrorAction SilentlyContinue
    Remove-Item Env:CRYPTO_LAB_EXTERNAL_RECEIPT_ROOTS -ErrorAction SilentlyContinue
    $apiKey = $null
    $apiSecret = $null
}
