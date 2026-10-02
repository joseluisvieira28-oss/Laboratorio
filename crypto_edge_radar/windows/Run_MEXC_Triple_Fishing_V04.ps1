param([string]$BundleRoot = $PSScriptRoot)

$ErrorActionPreference = "Stop"
$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV04"
$receiptRoot = Join-Path $runtime "live_receipts\operator_futures_v04"
$stateDir = Join-Path $runtime "live_state"
New-Item -ItemType Directory -Force -Path $receiptRoot,$stateDir | Out-Null

$exe = Join-Path $BundleRoot "MEXCTripleFishingOperatorV04.exe"
$policy = Join-Path $BundleRoot "TRIPLE_FISHING_MULTI_SLOT_SMALL_AGGRESSIVE_V04.json"
$authority = Join-Path $runtime "OPERATOR_FUTURES_GLOBAL_AUTHORITY_V04_ACTIVE.json"
$ready = Join-Path $stateDir "triple_ready_v04.json"
$armed = Join-Path $runtime "OPERATOR_FUTURES_V04_ARMED.json"
$kill = Join-Path $runtime "OPERATOR_FUTURES_V04_KILL_SWITCH"
$ledger = Join-Path $stateDir "MULTI_SLOT_LEDGER_V04.json"

if (-not (Test-Path -LiteralPath $exe)) { throw "Missing V0.4 executor: $exe" }
if (-not (Test-Path -LiteralPath $authority)) { throw "V0.4 ACTIVE authority missing. Do not bypass." }
if (-not (Test-Path -LiteralPath $armed)) { throw "V0.4 is not armed. Do not bypass." }
if (-not (Test-Path -LiteralPath $ready)) { throw "V0.4 readiness receipt missing." }

$secretDir = Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
function Unprotect-LocalSecret {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Missing local DPAPI secret: $Path" }
    $cipher = Get-Content -Raw -LiteralPath $Path
    $secure = ConvertTo-SecureString $cipher
    $cred = New-Object System.Management.Automation.PSCredential("local", $secure)
    return $cred.GetNetworkCredential().Password
}

$apiKey=$null
$apiSecret=$null
try {
    $apiKey=Unprotect-LocalSecret (Join-Path $secretDir "mexc_api_key.dpapi")
    $apiSecret=Unprotect-LocalSecret (Join-Path $secretDir "mexc_api_secret.dpapi")
    $env:MEXC_API_KEY=$apiKey
    $env:MEXC_API_SECRET=$apiSecret

    & $exe --receipt-root $receiptRoot --policy $policy --activation-authority $authority --readiness-receipt $ready --armed-path $armed --kill-switch $kill --ledger-path $ledger --engine-status (Join-Path $stateDir "operator_futures_engine_v04.json") --supervisor-state (Join-Path $stateDir "triple_fishing_operator_v04.json") --bnb-state (Join-Path $stateDir "bnb_operator_source_v04.json") --options-db (Join-Path $stateDir "options_v21_operator_v04.sqlite3") --options-state (Join-Path $stateDir "options_v21_operator_source_v04.json") --dh03-market-db (Join-Path $stateDir "dh03_operator_market_v04.sqlite3") --dh03-evidence-db (Join-Path $stateDir "dh03_operator_evidence_v04.sqlite3") --dh03-state (Join-Path $stateDir "dh03_operator_source_v04.json")
    exit $LASTEXITCODE
}
finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    $apiKey=$null
    $apiSecret=$null
}
