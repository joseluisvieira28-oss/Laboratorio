param([switch]$Live)

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
function Require-Exe([string]$Name) {
  $p=Join-Path $Dist $Name
  if (-not (Test-Path $p)) { throw "Missing executable: $p" }
  return $p
}
function Invoke-JsonExe([string]$Exe,[string[]]$Args) {
  $raw=& $Exe @Args
  $rc=$LASTEXITCODE
  $text=($raw | Out-String).Trim()
  if ($text) { Write-Host $text }
  $obj=$null
  try { $obj=$text | ConvertFrom-Json } catch {}
  return @{ rc=$rc; obj=$obj; text=$text }
}

if (-not (Test-Path $keyPath) -or -not (Test-Path $secretPath) -or -not (Test-Path $bindingPath)) {
  throw "MEXC V0.3 secrets/binding missing. Run Set_MEXC_Tier2_Secrets_V03.ps1 first."
}
$apiKey=$null; $apiSecret=$null
try {
  $apiKey=Unprotect $keyPath; $apiSecret=Unprotect $secretPath
  $binding=Get-Content $bindingPath -Raw | ConvertFrom-Json
  $sha=[System.Security.Cryptography.SHA256]::Create()
  try {
    $actual=-join ($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($apiKey)) | ForEach-Object {$_.ToString("x2")})
  } finally { $sha.Dispose() }
  if ($actual -ne [string]$binding.api_key_sha256) { throw "LOCAL_API_KEY_BINDING_MISMATCH" }

  $env:MEXC_API_KEY=$apiKey
  $env:MEXC_API_SECRET=$apiSecret
  if ($Live) { $env:CRYPTO_LAB_LIVE_EXECUTION_TOKEN="CRYPTO_LAB_TIER2_MICROLIVE_V0_3" }
  else { Remove-Item Env:CRYPTO_LAB_LIVE_EXECUTION_TOKEN -ErrorAction SilentlyContinue }

  Push-Location $Root
  try {
    $signalPath=Join-Path $State "options_v21_execution_signal.json"
    $bridge=Invoke-JsonExe (Require-Exe "MEXCOptionsV21SignalBridge.exe") @("--out",$signalPath)
    if ($bridge.rc -ne 0) { exit $bridge.rc }
    $signal=Get-Content $signalPath -Raw | ConvertFrom-Json
    $direction=[string]$signal.signal_direction
    $authorityPath=Join-Path $State "options_v21_active_micro_live_authority.json"

    if ($direction -eq "SHORT") {
      $pf=Join-Path $State "mexc_tier2_futures_preflight_receipt.json"
      $risk=Join-Path $State "mexc_tier2_futures_risk_state.json"
      $r=Invoke-JsonExe (Require-Exe "MEXCTier2FuturesPreflight.exe") @("--binding-file",$bindingPath,"--out",$pf)
      if ($r.rc -ne 0) { exit $r.rc }
      $r=Invoke-JsonExe (Require-Exe "MEXCTier2RiskState.exe") @("--preflight",$pf,"--receipt-root",$Receipts,"--out",$risk)
      if ($r.rc -ne 0) { exit $r.rc }
      $r=Invoke-JsonExe (Require-Exe "MEXCOptionsAuthorityBuilder.exe") @(
        "--signal",$signalPath,
        "--long-template",(Join-Path $Root "OPTIONS_SPOTPERP_001_V21_MICROLIVE_LONG_SPOT_AUTHORITY_TEMPLATE_V0.3.json"),
        "--short-template",(Join-Path $Root "OPTIONS_SPOTPERP_001_V21_MICROLIVE_SHORT_AUTHORITY_TEMPLATE_V0.3.json"),
        "--futures-preflight",$pf,
        "--out",$authorityPath
      )
      if ($r.rc -ne 0) { exit $r.rc }
      $args=@("--authority",$authorityPath,"--preflight",$pf,"--signal",$signalPath,"--risk-state",$risk,"--receipt-root",$Receipts,"--duplicate-lock-root",(Join-Path $State "duplicate_locks"))
      if ($Live) { $args+= "--execute" }
      $exec=Invoke-JsonExe (Require-Exe "MEXCTier2LiveExecutor.exe") $args
      if ($exec.rc -ne 0) { exit $exec.rc }
      if ($Live -and $exec.obj.status -eq "FILLED_EXIT_PENDING") {
        $session=[string]$exec.obj.session_dir
        Start-Process -FilePath (Require-Exe "MEXCTier2ExitGuard.exe") -ArgumentList @(
          "--authority",$authorityPath,"--active-trade",(Join-Path $session "ACTIVE_TRADE_STATE.json"),
          "--session-dir",$session,"--watch","--execute"
        ) -WorkingDirectory $Root -WindowStyle Hidden
      }
    }
    elseif ($direction -eq "LONG") {
      $pf=Join-Path $State "mexc_spot_preflight_receipt.json"
      $risk=Join-Path $State "mexc_tier2_spot_risk_state.json"
      $spotPfExe=Require-Exe "MEXCSpotPreflight.exe"
      $raw=& $spotPfExe
      $rc=$LASTEXITCODE
      if (Test-Path (Join-Path $Root "mexc_spot_preflight_receipt.json")) {
        Move-Item -Force (Join-Path $Root "mexc_spot_preflight_receipt.json") $pf
      }
      if ($raw) { Write-Host (($raw|Out-String).Trim()) }
      if ($rc -ne 0) { exit $rc }
      $r=Invoke-JsonExe (Require-Exe "MEXCTier2SpotRiskState.exe") @("--preflight",$pf,"--receipt-root",$Receipts,"--out",$risk)
      if ($r.rc -ne 0) { exit $r.rc }
      $r=Invoke-JsonExe (Require-Exe "MEXCOptionsAuthorityBuilder.exe") @(
        "--signal",$signalPath,
        "--long-template",(Join-Path $Root "OPTIONS_SPOTPERP_001_V21_MICROLIVE_LONG_SPOT_AUTHORITY_TEMPLATE_V0.3.json"),
        "--short-template",(Join-Path $Root "OPTIONS_SPOTPERP_001_V21_MICROLIVE_SHORT_AUTHORITY_TEMPLATE_V0.3.json"),
        "--spot-preflight",$pf,
        "--out",$authorityPath
      )
      if ($r.rc -ne 0) { exit $r.rc }
      $args=@("--authority",$authorityPath,"--preflight",$pf,"--signal",$signalPath,"--risk-state",$risk,"--receipt-root",$Receipts,"--duplicate-lock-root",(Join-Path $State "duplicate_locks"))
      if ($Live) { $args+="--execute" }
      $exec=Invoke-JsonExe (Require-Exe "MEXCTier2SpotExecutor.exe") $args
      if ($exec.rc -ne 0) { exit $exec.rc }
      if ($Live -and $exec.obj.status -eq "FILLED_EXIT_PENDING") {
        $session=[string]$exec.obj.session_dir
        Start-Process -FilePath (Require-Exe "MEXCTier2SpotExitGuard.exe") -ArgumentList @(
          "--authority",$authorityPath,"--active-trade",(Join-Path $session "ACTIVE_TRADE_STATE.json"),
          "--session-dir",$session,"--watch","--execute"
        ) -WorkingDirectory $Root -WindowStyle Hidden
      }
    }
    else {
      Write-Host "FAIL_CLOSED: OPTIONS signal is not LONG or SHORT."
      exit 2
    }
  } finally { Pop-Location }
}
finally {
  Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
  Remove-Item Env:CRYPTO_LAB_LIVE_EXECUTION_TOKEN -ErrorAction SilentlyContinue
  $apiKey=$null; $apiSecret=$null
}
