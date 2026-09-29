param([string]$BundleRoot = $PSScriptRoot)

$ErrorActionPreference = "Stop"
$exe = Join-Path $BundleRoot "MEXCOperatorReadyV02.exe"
$policy = Join-Path $BundleRoot "OPERATOR_GLOBAL_RISK_V02.json"
$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\OperatorFuturesV02"
$receiptRoot = Join-Path $runtime "live_receipts"
$stateDir = Join-Path $runtime "live_state"
$armedPath = Join-Path $runtime "OPERATOR_FUTURES_V02_ARMED.json"
New-Item -ItemType Directory -Force -Path $runtime,$receiptRoot,$stateDir | Out-Null
if (-not (Test-Path -LiteralPath $exe)) { throw "MEXCOperatorReadyV02.exe missing: $exe" }
if (-not (Test-Path -LiteralPath $policy)) { throw "Policy missing: $policy" }

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
    $optionsReceipts = Join-Path $env:USERPROFILE "Desktop\OPTIONS_V21_FUTURES_ONLY_AUTOLIVE_V021\live_receipts\options_v21_futures"
    if (Test-Path -LiteralPath $optionsReceipts) { $env:CRYPTO_LAB_EXTERNAL_RECEIPT_ROOTS = $optionsReceipts }
    & $exe --policy $policy --receipt-root $receiptRoot --out (Join-Path $stateDir "operator_ready_v02.json") --armed-path $armedPath --arm
    exit $LASTEXITCODE
}
finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    $apiKey = $null
    $apiSecret = $null
}
