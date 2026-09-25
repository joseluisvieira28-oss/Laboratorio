param([switch]$Live)
$ErrorActionPreference="Stop"
$Root=Split-Path -Parent $PSScriptRoot
$Dist=Join-Path $Root "dist"
$Receipts=Join-Path $Root "live_receipts"
if (-not (Test-Path $Receipts)) { exit 0 }

if ((Get-Process -Name "MEXCTier2ExitGuard" -ErrorAction SilentlyContinue) -or (Get-Process -Name "MEXCTier2SpotExitGuard" -ErrorAction SilentlyContinue)) {
  Write-Host "Exit guard already running; recovery does not duplicate it."
  exit 0
}
$active=Get-ChildItem -Path $Receipts -Filter "ACTIVE_TRADE_STATE.json" -Recurse -ErrorAction SilentlyContinue |
  Where-Object { -not (Test-Path (Join-Path $_.Directory.FullName "POST_TRADE_RECONCILIATION.json")) }

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
