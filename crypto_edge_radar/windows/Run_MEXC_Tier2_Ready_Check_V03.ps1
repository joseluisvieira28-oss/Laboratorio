$ErrorActionPreference="Stop"

$Root=Split-Path -Parent $PSScriptRoot
$Dist=Join-Path $Root "dist"
$State=Join-Path $Root "live_state"
$Receipts=Join-Path $Root "live_receipts"
New-Item -ItemType Directory -Force -Path $State,$Receipts | Out-Null

$secretDir=Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
$keyPath=Join-Path $secretDir "mexc_api_key.dpapi"
$secretPath=Join-Path $secretDir "mexc_api_secret.dpapi"
$bindingPath=Join-Path $HOME ".crypto_edge_radar\mexc_account_binding.json"

function Unprotect([string]$Path) {
  $secure=ConvertTo-SecureString (Get-Content -Raw $Path)
  $cred=New-Object System.Management.Automation.PSCredential("local",$secure)
  return $cred.GetNetworkCredential().Password
}
if (-not (Test-Path $keyPath) -or -not (Test-Path $secretPath) -or -not (Test-Path $bindingPath)) {
  throw "V0.3 secrets/binding missing. Run Set_MEXC_Tier2_Secrets_V03.ps1 first."
}

$apiKey=$null; $apiSecret=$null
try {
  $apiKey=Unprotect $keyPath; $apiSecret=Unprotect $secretPath
  $env:MEXC_API_KEY=$apiKey; $env:MEXC_API_SECRET=$apiSecret
  Push-Location $Root
  try {
    $fpf=Join-Path $State "mexc_tier2_futures_preflight_receipt.json"
    $frisk=Join-Path $State "mexc_tier2_futures_risk_state.json"
    & (Join-Path $Dist "MEXCTier2FuturesPreflight.exe") --binding-file $bindingPath --out $fpf
    $fpfExit=$LASTEXITCODE
    if (Test-Path $fpf) { $fp=Get-Content $fpf -Raw | ConvertFrom-Json } else { $fp=$null }

    if ($null -ne $fp -and $fp.pass -eq $true) {
      & (Join-Path $Dist "MEXCTier2RiskState.exe") --preflight $fpf --receipt-root $Receipts --out $frisk
      $friskExit=$LASTEXITCODE
      $fr=Get-Content $frisk -Raw | ConvertFrom-Json
      $venueMin=[double]$fp.checks.contract.minimum_executable_notional_estimate_usdt
      $futuresReady=($fr.status -eq "PASS" -and $venueMin -le 10.0)
    } else {
      $fr=$null; $venueMin=$null; $futuresReady=$false
    }

    $spotTemp=Join-Path $Root "mexc_spot_preflight_receipt.json"
    Remove-Item $spotTemp -Force -ErrorAction SilentlyContinue
    & (Join-Path $Dist "MEXCSpotPreflight.exe")
    $spotExit=$LASTEXITCODE
    $spf=Join-Path $State "mexc_spot_preflight_receipt.json"
    if (Test-Path $spotTemp) { Move-Item -Force $spotTemp $spf }
    if (Test-Path $spf) { $sp=Get-Content $spf -Raw | ConvertFrom-Json } else { $sp=$null }
    $srisk=Join-Path $State "mexc_tier2_spot_risk_state.json"
    if ($null -ne $sp -and $sp.pass -eq $true) {
      & (Join-Path $Dist "MEXCTier2SpotRiskState.exe") --preflight $spf --receipt-root $Receipts --out $srisk
      $sriskExit=$LASTEXITCODE
      $sr=Get-Content $srisk -Raw | ConvertFrom-Json
      $sc=$sp.candidate_feasibility.'OPTIONS-SPOTPERP-001-V2.1-LONG'
      $spotReady=($sr.status -eq "PASS" -and $sc.pass -eq $true)
    } else {
      $sr=$null; $sc=$null; $spotReady=$false
    }

    Write-Host ""
    Write-Host "================= OPTIONS V2.1 MICRO-LIVE V0.3 READY CHECK ================="
    Write-Host ("SHORT / MEXC FUTURES 1x : " + $(if($futuresReady){"READY"}else{"BLOCKED"}))
    if ($null -ne $venueMin) { Write-Host ("  Venue min / cap       : " + [math]::Round($venueMin,4) + " / 10.0000 USDT") }
    if ($null -ne $fr) {
      Write-Host ("  Risk firewall         : " + $fr.status)
      Write-Host ("  Daily loss            : " + [math]::Round([double]$fr.daily_realized_loss_usdt,4) + " / 2.0000")
      Write-Host ("  Rolling 7d loss       : " + [math]::Round([double]$fr.rolling_7d_realized_loss_usdt,4) + " / 5.0000")
    }
    if ($null -ne $fp -and $fp.pass -ne $true) { Write-Host ("  Blockers              : " + (($fp.blockers|ForEach-Object {$_}) -join ", ")) }

    Write-Host ("LONG / MEXC SPOT       : " + $(if($spotReady){"READY"}else{"BLOCKED"}))
    if ($null -ne $sp) {
      Write-Host ("  Spot global preflight : " + $sp.status)
      Write-Host ("  Free Spot USDT        : " + [math]::Round([double]$sp.checks.account.usdt_free,4))
      if ($null -ne $sc -and $sc.pass -ne $true) { Write-Host ("  Candidate blockers    : " + (($sc.blockers|ForEach-Object {$_}) -join ", ")) }
      if ($sp.pass -ne $true) { Write-Host ("  Global blockers       : " + (($sp.blockers|ForEach-Object {$_}) -join ", ")) }
    }
    if ($null -ne $sr) {
      Write-Host ("  Risk firewall         : " + $sr.status)
    }

    Write-Host "----------------------------------------------------------------------------"
    if ($futuresReady -or $spotReady) {
      Write-Host "STATE: AT_LEAST_ONE_LANE_READY"
      Write-Host "No real order was created by this ready-check."
      exit 0
    } else {
      Write-Host "STATE: BOTH_LANES_BLOCKED / NO ORDER"
      exit 2
    }
  } finally { Pop-Location }
}
finally {
  Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
  $apiKey=$null; $apiSecret=$null
}
