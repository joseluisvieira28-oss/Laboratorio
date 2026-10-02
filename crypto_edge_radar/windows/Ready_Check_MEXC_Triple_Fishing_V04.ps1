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

    & $readyExe --policy $policy --ledger $ledger --kill-switch $kill --legacy-v03-armed-path $legacyV03Armed --legacy-options-armed-path $legacyOptionsArmed --legacy-bnb-armed-path $legacyBnbArmed --out $out
    $rc=$LASTEXITCODE
    Write-Host ""
    Write-Host "=== V0.4 READY CHECK RECEIPT ==="
    if (Test-Path -LiteralPath $out) { Get-Content -Raw -LiteralPath $out }
    exit $rc
}
finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    $apiKey=$null
    $apiSecret=$null
}
