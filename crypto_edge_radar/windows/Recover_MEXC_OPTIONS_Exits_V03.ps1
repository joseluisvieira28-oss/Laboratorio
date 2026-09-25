param([switch]$Live)
$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
$Dist=Join-Path $Root "dist"
$Receipts=Join-Path $Root "live_receipts"
if (-not (Test-Path $Receipts)) { exit 0 }

$secretDir=Join-Path $env:LOCALAPPDATA "CryptoEdgeRadar\secrets"
$keyPath=Join-Path $secretDir "mexc_api_key.dpapi"
$secretPath=Join-Path $secretDir "mexc_api_secret.dpapi"
$bindingPath=Join-Path $HOME ".crypto_edge_radar\mexc_account_binding.json"
function Unprotect([string]$Path) {
  $secure=ConvertTo-SecureString (Get-Content -Raw $Path)
  $cred=New-Object System.Management.Automation.PSCredential("local",$secure)
  return $cred.GetNetworkCredential().Password
}

if ((Get-Process -Name "MEXCTier2ExitGuard" -ErrorAction SilentlyContinue) -or (Get-Process -Name "MEXCTier2SpotExitGuard" -ErrorAction SilentlyContinue)) {
  Write-Host "Exit guard already running; recovery does not duplicate it."
  exit 0
}
$active=Get-ChildItem -Path $Receipts -Filter "ACTIVE_TRADE_STATE.json" -Recurse -ErrorAction SilentlyContinue |
  Where-Object { -not (Test-Path (Join-Path $_.Directory.FullName "POST_TRADE_RECONCILIATION.json")) }

if ($Live -and $active.Count -gt 0) {
  if (-not (Test-Path $keyPath) -or -not (Test-Path $secretPath) -or -not (Test-Path $bindingPath)) {
    throw "Cannot recover live exit: DPAPI secrets/binding missing."
  }
  $apiKey=Unprotect $keyPath
  $apiSecret=Unprotect $secretPath
  $binding=Get-Content $bindingPath -Raw | ConvertFrom-Json
  $sha=[System.Security.Cryptography.SHA256]::Create()
  try { $actual=-join ($sha.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($apiKey)) | ForEach-Object {$_.ToString("x2")}) }
  finally { $sha.Dispose() }
  if ($actual -ne [string]$binding.api_key_sha256) { throw "LOCAL_API_KEY_BINDING_MISMATCH" }
  $env:MEXC_API_KEY=$apiKey
  $env:MEXC_API_SECRET=$apiSecret
  $env:CRYPTO_LAB_LIVE_EXECUTION_TOKEN="CRYPTO_LAB_TIER2_MICROLIVE_V0_3"
}

foreach ($file in $active) {
  $row=Get-Content $file.FullName -Raw | ConvertFrom-Json
  if ([string]$row.state -ne "EXIT_PENDING") { continue }
  if (-not $Live) {
    Write-Host ("ACTIVE TRADE NEEDS EXIT GUARD BUT RECOVERY IS DRY-RUN: " + $file.FullName)
    continue
  }
  $authority=[string]$row.authority_path
  if (-not (Test-Path $authority)) { throw "Active trade authority missing: $authority" }
  $translation=[string]$row.execution_translation
  if ($translation -like "POSITIVE_SIGNAL_TO_MEXC_SPOT*") { $exe=Join-Path $Dist "MEXCTier2SpotExitGuard.exe" }
  elseif ($translation -like "NEGATIVE_SIGNAL_TO_MEXC_USDT_PERPETUAL*") { $exe=Join-Path $Dist "MEXCTier2ExitGuard.exe" }
  else { throw "Unknown active execution translation: $translation" }

  Start-Process -FilePath $exe -ArgumentList @(
    "--authority",$authority,
    "--active-trade",$file.FullName,
    "--session-dir",$file.Directory.FullName,
    "--watch","--execute"
  ) -WorkingDirectory $Root -WindowStyle Hidden
  Write-Host ("Recovered exit guard: " + $file.Directory.FullName)
}

if ($Live) {
  Remove-Item Env:MEXC_API_KEY -ErrorAction SilentlyContinue
  Remove-Item Env:MEXC_API_SECRET -ErrorAction SilentlyContinue
  Remove-Item Env:CRYPTO_LAB_LIVE_EXECUTION_TOKEN -ErrorAction SilentlyContinue
  $apiKey=$null; $apiSecret=$null
}
