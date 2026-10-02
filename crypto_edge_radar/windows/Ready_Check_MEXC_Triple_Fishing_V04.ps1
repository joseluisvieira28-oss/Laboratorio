param([string]$BundleRoot = $PSScriptRoot)

$ErrorActionPreference = "Stop"
$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV04"
$stateDir = Join-Path $runtime "live_state"
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

$readyExe = Join-Path $BundleRoot "MEXCTripleFishingMultiSlotReadyV04.exe"
$policy = Join-Path $BundleRoot "TRIPLE_FISHING_MULTI_SLOT_SMALL_AGGRESSIVE_V04.json"
$ledger = Join-Path $stateDir "MULTI_SLOT_LEDGER_V04.json"
$kill = Join-Path $runtime "OPERATOR_FUTURES_V04_KILL_SWITCH"
$out = Join-Path $stateDir "triple_ready_v04.json"
$receiptRoot = Join-Path $runtime "live_receipts\operator_futures_v04"
New-Item -ItemType Directory -Force -Path $receiptRoot | Out-Null
$v03Runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV03"
$v03Receipts = Join-Path $v03Runtime "live_receipts\operator_futures_v03"
$v03Archive = Join-Path $v03Runtime "historical_options_receipts"
$v03Overlay = Join-Path $v03Runtime "live_state\OPTIONS_V21_PNL_CORRECTION_OVERLAY_V01.json"
$legacyBnbReceipts = Join-Path $env:LOCALAPPDATA "CryptoLab\OperatorFuturesV02\live_receipts"

$legacyV03Armed = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV03\OPERATOR_FUTURES_V03_ARMED.json"
$legacyBnbArmed = Join-Path $env:LOCALAPPDATA "CryptoLab\OperatorFuturesV02\OPERATOR_FUTURES_V02_ARMED.json"
$legacyOptionsArmed = Join-Path $env:USERPROFILE "Desktop\OPTIONS_V21_FUTURES_ONLY_AUTOLIVE_V021\AUTO_MICROLIVE_FUTURES_ARMED.json"

if (-not (Test-Path -LiteralPath $readyExe)) { throw "Missing readiness executable: $readyExe" }
if (-not (Test-Path -LiteralPath $policy)) { throw "Missing V0.4 policy: $policy" }

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

    $readyArgs = @("--policy",$policy,"--ledger",$ledger,"--kill-switch",$kill,"--receipt-root",$receiptRoot,"--legacy-v03-armed-path",$legacyV03Armed,"--legacy-options-armed-path",$legacyOptionsArmed,"--legacy-bnb-armed-path",$legacyBnbArmed,"--out",$out)
    foreach ($root in @($v03Receipts,$v03Archive,$legacyBnbReceipts)) {
        if (Test-Path -LiteralPath $root) { $readyArgs += @("--legacy-receipt-root",$root) }
    }
    if (Test-Path -LiteralPath $v03Archive) {
        if (-not (Test-Path -LiteralPath $v03Overlay)) { throw "Historical OPTIONS receipts exist but correction overlay is missing: $v03Overlay" }
        $readyArgs += @("--correction-overlay",$v03Overlay)
    }
    & $readyExe @readyArgs
    $rc=$LASTEXITCODE
    Write-Host ""
    Write-Host "=== V0.4 READY CHECK RECEIPT ==="
    if (Test-Path -LiteralPath $out) {
        Get-Content -Raw -LiteralPath $out
        $readyHash = (Get-FileHash -LiteralPath $out -Algorithm SHA256).Hash.ToLower()
        Write-Host ("READY_RECEIPT_SHA256=" + $readyHash)
    }
    exit $rc
}
finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    $apiKey=$null
    $apiSecret=$null
}
