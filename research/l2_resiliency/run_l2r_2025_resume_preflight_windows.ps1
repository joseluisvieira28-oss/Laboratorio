param(
  [Parameter(Mandatory=$true)][string]$PackagePath,
  [string]$InventoryPath = "",
  [string]$RunnerPath = "",
  [string]$AwsProfile = ""
)

$ErrorActionPreference = "Stop"
$ExpectedPackage = "3da0f466b1db170f8aedc7d45f7b757bb4e843cc7695bffc9953908c21449ba6"
$ExpectedRunner  = "80347c42e1893fbe0284ccc5779fdd841362a3feb24644d39777144f15be2a55"

Write-Host "L2-RESILIENCY-001 — SAFE RESUME PREFLIGHT" -ForegroundColor Cyan
Write-Host "No market outcomes are opened by this script."

if (-not (Test-Path -LiteralPath $PackagePath)) { throw "Frozen V0.1.1 package not found: $PackagePath" }
$pkgHash=(Get-FileHash -Algorithm SHA256 -LiteralPath $PackagePath).Hash.ToLowerInvariant()
if ($pkgHash -ne $ExpectedPackage) { throw "FAIL CLOSED: package SHA256 mismatch. Observed $pkgHash" }
Write-Host "PASS package SHA256" -ForegroundColor Green

if ($RunnerPath) {
  if (-not (Test-Path -LiteralPath $RunnerPath)) { throw "Runner not found: $RunnerPath" }
  $runnerHash=(Get-FileHash -Algorithm SHA256 -LiteralPath $RunnerPath).Hash.ToLowerInvariant()
  if ($runnerHash -ne $ExpectedRunner) { throw "FAIL CLOSED: runner SHA256 mismatch. Observed $runnerHash" }
  Write-Host "PASS runner SHA256" -ForegroundColor Green
}

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
  throw "AWS CLI not found. Install/configure it before source acquisition."
}

$awsArgs=@("sts","get-caller-identity","--output","json")
if ($AwsProfile) { $awsArgs += @("--profile",$AwsProfile) }
try {
  $identity = & aws @awsArgs 2>$null | ConvertFrom-Json
  if (-not $identity.Account -or -not $identity.Arn) { throw "identity response incomplete" }
  Write-Host ("PASS AWS auth — account {0}; ARN {1}" -f $identity.Account,$identity.Arn) -ForegroundColor Green
  Write-Host "Credentials are not printed."
} catch {
  throw "AWS authentication is not ready. Reauthenticate the legitimate requester-pays profile, then rerun this preflight. Nothing was downloaded."
}

$python=(Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) { $python=(Get-Command py -ErrorAction SilentlyContinue) }
if (-not $python) { throw "Python not found." }

$script=Join-Path $PSScriptRoot "l2r_2025_resume_offline_preflight_v01.py"
$argsList=@($script,"--package",$PackagePath)
if ($InventoryPath) { $argsList += @("--inventory",$InventoryPath,"--allow-progress") }
if ($RunnerPath) { $argsList += @("--runner",$RunnerPath) }

& $python.Source @argsList
if ($LASTEXITCODE -ne 0) { throw "Offline resume preflight failed with exit code $LASTEXITCODE" }

Write-Host ""
Write-Host "READY_FOR_EXACT_V011_RESUME" -ForegroundColor Green
Write-Host "This helper does NOT launch the frozen validation package automatically."
Write-Host "Run the exact V0.1.1 package only after this preflight passes."
