param(
  [string]$Base = "$env:USERPROFILE\Desktop\L2R_2025_BTC_VALIDATION_LOCAL"
)
$ErrorActionPreference = 'Stop'
$ExpectedScriptSha = '62c88b86c82b80cf10c203258a9444192eb30b9ff6c4b9247a600d3a21d175f8'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Runner = Join-Path $Here 'l2r_exec_passive_upper_bound_v01.py'
Write-Host '=== L2R EXEC PASSIVE UPPER-BOUND V0.1 ==='
Write-Host '2025 DEVELOPMENT ONLY | NO 2026 | NO NETWORK | NO ORDERS | NO EXCHANGE MUTATION'
if (!(Test-Path -LiteralPath $Runner)) { throw "Runner missing: $Runner" }
$sha=(Get-FileHash -Algorithm SHA256 -LiteralPath $Runner).Hash.ToLower()
if ($sha -ne $ExpectedScriptSha) { throw "FAIL-CLOSED runner SHA mismatch: $sha" }
Write-Host "RUNNER SHA PASS $sha"
$manifest=Join-Path $Base '_EVIDENCE_2025_VALIDATION_V0_1\L2_RESILIENCY_001_2025_BTC_RAW_MANIFEST_V0_1.csv'
if (!(Test-Path -LiteralPath $manifest)) { throw "Canonical manifest missing: $manifest" }
$py=$null
foreach($c in @('py','python','python3')) {
  try { & $c --version *> $null; if($LASTEXITCODE -eq 0){$py=$c;break} } catch {}
}
if(!$py){ throw 'Python 3 not found.' }
& $py -c "import lz4.frame" 2>$null
if($LASTEXITCODE -ne 0){
  Write-Host 'Installing lz4 dependency...'
  & $py -m pip install 'lz4==4.4.4'
  if($LASTEXITCODE -ne 0){ throw 'Could not install lz4.' }
}
Write-Host "EXECUTING against Base=$Base"
& $py $Runner --base $Base
if($LASTEXITCODE -ne 0){ throw "Diagnostic failed rc=$LASTEXITCODE" }
Write-Host '=== L2R EXEC PASSIVE V0.1 COMPLETE ==='
