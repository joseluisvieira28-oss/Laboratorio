param(
  [string]$Base = "$env:USERPROFILE\Desktop\L2R_2025_BTC_VALIDATION_LOCAL"
)
$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Artifact = Join-Path $Here 'ETF_CME_INSTFLOW_001_OOS_2025.zip'
$Runner = Join-Path $Here 'l2r_overlay_etf_cme_2025_development_v01.py'
$ExpectedArtifactSha = '40bd341c300532e5b67127a098c82ecf2f41e1cc4a3ce646ac824b27529f9bd1'
$ExpectedRunnerSha = '495129040193b01218d867bd8a29f50039e5229203d118571f38445746942b2a'
$RunnerUrl = 'https://raw.githubusercontent.com/joseluisvieira28-oss/Laboratorio/l2r-overlay-etf-cme-v0.1/research/l2_resiliency_overlay/l2r_overlay_etf_cme_2025_development_v01.py'

Write-Host '=== L2R OVERLAY ETF-CME V0.1 — 2025 DEVELOPMENT ==='
Write-Host 'DEVELOPMENT ONLY | NO 2026 | NO ORDERS | NO EXCHANGE MUTATION | NO MAIN MERGE'

if (!(Test-Path -LiteralPath $Artifact)) { throw "Missing bundled ETF artifact: $Artifact" }
$aSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Artifact).Hash.ToLower()
if ($aSha -ne $ExpectedArtifactSha) { throw "FAIL-CLOSED ETF artifact SHA mismatch: $aSha" }
Write-Host "ETF ARTIFACT SHA PASS $aSha"

$needRunner = $true
if (Test-Path -LiteralPath $Runner) {
  $rSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Runner).Hash.ToLower()
  if ($rSha -eq $ExpectedRunnerSha) { $needRunner = $false }
}
if ($needRunner) {
  $tmp = "$Runner.tmp"
  Invoke-WebRequest -UseBasicParsing -Uri $RunnerUrl -OutFile $tmp
  $rSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $tmp).Hash.ToLower()
  if ($rSha -ne $ExpectedRunnerSha) {
    Remove-Item -Force $tmp -ErrorAction SilentlyContinue
    throw "FAIL-CLOSED downloaded runner SHA mismatch: $rSha"
  }
  Move-Item -Force $tmp $Runner
}
$rSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $Runner).Hash.ToLower()
if ($rSha -ne $ExpectedRunnerSha) { throw "FAIL-CLOSED runner SHA mismatch: $rSha" }
Write-Host "RUNNER SHA PASS $rSha"

$py = $null
foreach ($c in @('py','python','python3')) {
  try { & $c --version *> $null; if ($LASTEXITCODE -eq 0) { $py=$c; break } } catch {}
}
if (!$py) { throw 'Python 3 not found.' }

& $py -c "import lz4.frame" 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host 'Installing lz4 dependency...'
  & $py -m pip install 'lz4==4.4.4'
  if ($LASTEXITCODE -ne 0) { throw 'Could not install lz4.' }
}

Write-Host "BASE: $Base"
& $py $Runner --base $Base --etf-artifact $Artifact
if ($LASTEXITCODE -ne 0) { throw "Overlay diagnostic failed rc=$LASTEXITCODE" }

$Evidence = Join-Path $Base 'L2R_OVERLAY_ETF_CME_001_2025_DEVELOPMENT_EVIDENCE_V0_1.zip'
if (!(Test-Path -LiteralPath $Evidence)) { throw "Expected evidence ZIP not produced: $Evidence" }
Write-Host ''
Write-Host '=== OVERLAY RUN COMPLETE ==='
Write-Host "EVIDENCE: $Evidence"
Write-Host ("SHA256: " + (Get-FileHash -Algorithm SHA256 -LiteralPath $Evidence).Hash.ToLower())
Write-Host 'Upload the evidence ZIP to ChatGPT for canonical adjudication.'
