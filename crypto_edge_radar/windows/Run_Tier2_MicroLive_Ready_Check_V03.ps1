param(
    [string]$RadarRoot = "$env:USERPROFILE\Desktop\CryptoEdgeRadar_V01433_FINAL"
)
$ErrorActionPreference = "Stop"
$PackRoot = Split-Path -Parent $PSScriptRoot
$Dist = Join-Path $PackRoot "dist"
$SecretDir = Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
$KeyPath = Join-Path $SecretDir "mexc_api_key.dpapi"
$SecretPath = Join-Path $SecretDir "mexc_api_secret.dpapi"

function Unprotect-LocalSecret([string]$Path) {
    $cipher = Get-Content -Raw -Path $Path
    $secure = ConvertTo-SecureString $cipher
    $credential = New-Object System.Management.Automation.PSCredential("local", $secure)
    return $credential.GetNetworkCredential().Password
}

Write-Host ""
Write-Host "================ CRYPTO LAB LIVE-GO READY CHECK V0.3 ================"
Write-Host "This command DOES NOT place an order."
Write-Host "Policy: Tier2 micro-live <=10 USDT, one position, no leverage >1x."
Write-Host ""

$radarPass=$false
$statusPath=Join-Path $RadarRoot "data\radar_status.json"
if (Test-Path $statusPath) {
    $rs=Get-Content $statusPath -Raw | ConvertFrom-Json
    $build=[string]$rs.Build
    if ([string]::IsNullOrWhiteSpace($build)) { $build=[string]$rs.build_id }
    $registry=[string]$rs.RegistryVersion
    if ([string]::IsNullOrWhiteSpace($registry)) { $registry=[string]$rs.registry_version }
    $loaded=[int]($rs.FocusLoaded)
    if (-not $loaded) { $loaded=[int]($rs.focus_loaded) }
    $expected=[int]($rs.FocusExpected)
    if (-not $expected) { $expected=[int]($rs.focus_expected) }
    Write-Host "Radar build             : $build"
    Write-Host "Radar registry          : $registry"
    Write-Host "Radar focus             : $loaded / $expected"
    $radarPass=($build -match "0\.14\.4" -and $registry -eq "3.7" -and $loaded -eq 8 -and $expected -eq 8)
} else {
    Write-Host "Radar status            : MISSING $statusPath"
}
try {
    $http=Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8787/" -TimeoutSec 4
    Write-Host "Radar HTTP              : PASS $($http.StatusCode)"
    $radarPass=$radarPass -and ($http.StatusCode -eq 200)
} catch {
    Write-Host "Radar HTTP              : FAIL"
    $radarPass=$false
}

if (-not (Test-Path $KeyPath) -or -not (Test-Path $SecretPath)) {
    Write-Host "MEXC secrets            : MISSING (run Set_MEXC_Preflight_Secrets.ps1)"
    Write-Host "STATE                    : BLOCKED"
    exit 2
}

$apiKey=$null
$apiSecret=$null
try {
    $apiKey=Unprotect-LocalSecret $KeyPath
    $apiSecret=Unprotect-LocalSecret $SecretPath
    $env:MEXC_API_KEY=$apiKey
    $env:MEXC_API_SECRET=$apiSecret

    $dataDir=Join-Path $RadarRoot "data"
    $receipts=Join-Path $RadarRoot "live_receipts"
    New-Item -ItemType Directory -Force -Path $dataDir,$receipts | Out-Null
    $spotReceipt=Join-Path $dataDir "mexc_spot_authenticated_preflight_receipt.json"
    $riskReceipt=Join-Path $dataDir "mexc_account_risk_state.json"

    $spotExe=Join-Path $Dist "MEXCSpotAuthenticatedPreflight.exe"
    if (-not (Test-Path $spotExe)) { throw "MEXCSpotAuthenticatedPreflight.exe missing" }
    & $spotExe --out $spotReceipt
    $spotExit=$LASTEXITCODE
    if (-not (Test-Path $spotReceipt)) { throw "Spot preflight receipt missing" }
    $spot=Get-Content $spotReceipt -Raw | ConvertFrom-Json

    $riskExe=Join-Path $Dist "MEXCRiskState.exe"
    if (-not (Test-Path $riskExe)) { throw "MEXCRiskState.exe missing" }
    & $riskExe --preflight $spotReceipt --receipt-root $receipts --out $riskReceipt
    $riskExit=$LASTEXITCODE
    if (-not (Test-Path $riskReceipt)) { throw "Risk receipt missing" }
    $risk=Get-Content $riskReceipt -Raw | ConvertFrom-Json

    Write-Host ""
    Write-Host "Radar V0.14.4 / 8 motors : $(if($radarPass){'PASS'}else{'BLOCKED'})"
    Write-Host "MEXC Spot preflight       : $($spot.status)"
    Write-Host "BTCUSDT API trading       : $($spot.checks.symbol.pass)"
    Write-Host "Account fee gate STRESS20 : $($spot.checks.fees.pass)"
    Write-Host "MX fee deduction enabled  : $($spot.checks.fees.mx_deduct_enabled)"
    Write-Host "USDT free                 : $($spot.checks.account.usdt_free)"
    Write-Host "Open BTCUSDT Spot orders  : $($spot.checks.orders.open_order_count)"
    Write-Host "Risk firewall             : $($risk.status)"
    Write-Host "Daily realized loss USDT  : $($risk.daily_realized_loss_usdt) / 2"
    Write-Host "7d realized loss USDT     : $($risk.weekly_realized_loss_usdt) / 5"
    Write-Host "Live notional active USDT : $($risk.concurrent_planned_notional_usdt) / 10"
    Write-Host "Open micro-live positions : $($risk.open_micro_live_positions) / 1"
    Write-Host "--------------------------------------------------------------------"

    if ($radarPass -and $spot.pass -eq $true -and $risk.status -eq "PASS") {
        Write-Host "STATE: INFRA_ARMED__WAITING_CANONICAL_TIER2_SIGNAL"
        Write-Host "Next valid OPTIONS LONG signal can enter exact order-test + active-authority gate."
        exit 0
    }
    Write-Host "STATE: BLOCKED__NO_ORDER"
    exit 2
}
finally {
    Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
    $apiKey=$null
    $apiSecret=$null
}
