param([string]$BundleRoot = $PSScriptRoot)

$ErrorActionPreference = "Stop"
$runtime = Join-Path $env:LOCALAPPDATA "CryptoLab\TripleFishingV03"
$receiptRoot = Join-Path $runtime "live_receipts\operator_futures_v03"
$stateDir = Join-Path $runtime "live_state"
$overlay = Join-Path $stateDir "OPTIONS_V21_PNL_CORRECTION_OVERLAY_V01.json"
$armed = Join-Path $runtime "OPERATOR_FUTURES_V03_ARMED.json"
$kill = Join-Path $runtime "OPERATOR_FUTURES_V03_KILL_SWITCH"
$slot = Join-Path $stateDir "GLOBAL_POSITION_SLOT_V03.json"
$readyExe = Join-Path $BundleRoot "MEXCTripleFishingReadyV03.exe"

$legacyBnbArmed = Join-Path $env:LOCALAPPDATA "CryptoLab\OperatorFuturesV02\OPERATOR_FUTURES_V02_ARMED.json"
$legacyOptionsArmed = Join-Path $env:USERPROFILE "Desktop\OPTIONS_V21_FUTURES_ONLY_AUTOLIVE_V021\AUTO_MICROLIVE_FUTURES_ARMED.json"

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
    $env:CRYPTO_LAB_PNL_CORRECTION_OVERLAY=$overlay
    $roots=@((Join-Path $runtime "historical_options_receipts"))
    $legacyBnbReceipts=Join-Path $env:LOCALAPPDATA "CryptoLab\OperatorFuturesV02\live_receipts"
    if (Test-Path -LiteralPath $legacyBnbReceipts) { $roots += $legacyBnbReceipts }
    $env:CRYPTO_LAB_EXTERNAL_RECEIPT_ROOTS=($roots -join [IO.Path]::PathSeparator)

    $readyArgs = @(
        "--receipt-root",$receiptRoot,
        "--correction-overlay",$overlay,
        "--supervisor-state",(Join-Path $stateDir "triple_fishing_operator_v03.json"),
        "--global-slot-path",$slot,
        "--armed-path",$armed,
        "--kill-switch",$kill,
        "--legacy-bnb-armed-path",$legacyBnbArmed,
        "--legacy-options-armed-path",$legacyOptionsArmed,
        "--out",(Join-Path $stateDir "triple_ready_v03.json"),
        "--arm"
    )
    & $readyExe @readyArgs
    exit $LASTEXITCODE
}
finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    Remove-Item Env:CRYPTO_LAB_PNL_CORRECTION_OVERLAY -ErrorAction SilentlyContinue
    Remove-Item Env:CRYPTO_LAB_EXTERNAL_RECEIPT_ROOTS -ErrorAction SilentlyContinue
    $apiKey=$null
    $apiSecret=$null
}
