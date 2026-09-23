param(
  [string]$PartsRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$LabId = "L2-RESILIENCY-001"
$Base = Join-Path $env:USERPROFILE "Desktop\L2R_2025_BTC_VALIDATION_LOCAL"
$RawRoot = Join-Path $Base "HL_L2R_2025_BTC_RAW_V0_1"
$EvidenceRoot = Join-Path $Base "_EVIDENCE_2025_VALIDATION_V0_1"
$TmpRoot = Join-Path $Base "_DRIVE_RESTORE_TMP_V01A"
$MasterName = "L2R_2025_DRIVE_PARTS_MASTER_MANIFEST.json"
$ExpectedManifestSha = "767e75594864344c75dd2669ec4fad8c738710c218322b11fd43a83077ef17c3"
$ExpectedObjects = 8400
$ExpectedBytes = [int64]8975275014
$ExpectedPackageSha = "bb6195b42f2ad75ddc7ea8eefe4ecabe5bcc940ec8e3e14b22e4e1dc9c075fc8"

$ExpectedArchives = @{
  "20250530.zip" = @{ Size=[int64]3090700320; Sha="1f5c59b04cf8a51638a32f0aa7ffd7b5a29a6906bd4f3a3881df716b4bbbabce" }
  "20250907.zip" = @{ Size=[int64]2088567760; Sha="b1aeda17292fc4358a7f396a683a27c46c769df71e74baf47a463d1b871f28a3" }
  "20251227.zip" = @{ Size=[int64]2333757454; Sha="0683727131ac8e3cbc45a47edd57fd9ec69a996eb5eaed40a2ce6bda86d1b54c" }
}

$ExpectedMembers = @{
  "l2r_2025_source_clock_diagnostic_v01a.py" = "0f929df19a713d7fb1805688be15fa131ba9c270e9f9fd6c84776ed5b0f5531f"
  "RUN_2025_SOURCE_CLOCK_DIAGNOSTIC_V01A.bat" = "ed9682f5f3a28f31e7ad402189dda0adb0e4bab7f70370f82a5d91fb33bab25d"
  "README.txt" = "82a1b7ee881839e6f89a168920a49b8aa23e274270fc9935a12b5a8552b22059"
  "MANIFEST_EQUIVALENCE_RECEIPT_V0_1A.json" = "51441b8a547892b711085666ac1f698130a3e9960ace59a861d15b9b2385e0d9"
}

function Sha256([string]$Path) {
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Test-PartsRoot([string]$Path) {
  if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
  return (Test-Path -LiteralPath (Join-Path $Path $MasterName) -PathType Leaf)
}

function Find-PartsRoot {
  if (Test-PartsRoot $PartsRoot) { return (Resolve-Path -LiteralPath $PartsRoot).Path }

  $names = @("L2R_2025_DRIVE_PARTS_220MiB","L2R_2025_DRIVE_PARTS_32MiB")
  $candidates = New-Object System.Collections.Generic.List[string]
  foreach ($n in $names) {
    $candidates.Add((Join-Path $env:USERPROFILE $n))
    $candidates.Add((Join-Path $env:USERPROFILE ("My Drive\"+$n)))
    $candidates.Add((Join-Path $env:USERPROFILE ("Google Drive\My Drive\"+$n)))
  }

  foreach ($d in (Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue)) {
    foreach ($n in $names) {
      $candidates.Add((Join-Path $d.Root $n))
      $candidates.Add((Join-Path $d.Root ("My Drive\"+$n)))
    }
    $shared = Join-Path $d.Root "Shared drives"
    if (Test-Path -LiteralPath $shared -PathType Container) {
      foreach ($sd in (Get-ChildItem -LiteralPath $shared -Directory -ErrorAction SilentlyContinue)) {
        foreach ($n in $names) { $candidates.Add((Join-Path $sd.FullName $n)) }
      }
    }
  }

  foreach ($c in ($candidates | Select-Object -Unique)) {
    if (Test-PartsRoot $c) { return (Resolve-Path -LiteralPath $c).Path }
  }

  # Recursive fallback: Google Drive for Desktop often nests My Drive content
  # several folders below the mounted drive root. Search only the user profile
  # and non-system filesystem drives for the frozen master manifest.
  $searchRoots = New-Object System.Collections.Generic.List[string]
  if (Test-Path -LiteralPath $env:USERPROFILE -PathType Container) {
    $searchRoots.Add($env:USERPROFILE)
  }
  foreach ($d in (Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue)) {
    $root=[string]$d.Root
    if ([string]::IsNullOrWhiteSpace($root)) { continue }
    if ($root.TrimEnd('\') -ieq $env:SystemDrive) { continue }
    if (Test-Path -LiteralPath $root -PathType Container) { $searchRoots.Add($root) }
  }

  foreach ($root in ($searchRoots | Select-Object -Unique)) {
    Write-Host "Searching recursively for $MasterName under $root ..."
    try {
      $hit = Get-ChildItem -LiteralPath $root -Filter $MasterName -File -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 1
      if ($null -ne $hit) {
        $parent=$hit.Directory.FullName
        if (Test-PartsRoot $parent) {
          Write-Host "FOUND PartsRoot: $parent"
          return (Resolve-Path -LiteralPath $parent).Path
        }
      }
    } catch {
      Write-Host "  recursive search skipped/failed under $root : $($_.Exception.Message)"
    }
  }

  throw "Could not locate $MasterName. Google Drive may not be mounted/synced locally. Rerun with -PartsRoot 'X:\path\L2R_2025_DRIVE_PARTS_220MiB' once you know the local Drive path."
}

function Reassemble-Archive($Archive, [string]$Root, [string]$OutZip) {
  $name = [string]$Archive.source_file
  if (-not $ExpectedArchives.ContainsKey($name)) { throw "Unexpected archive in master manifest: $name" }
  $expected = $ExpectedArchives[$name]
  $expectedSize = [int64]$expected.Size
  $expectedSha = [string]$expected.Sha

  if (Test-Path -LiteralPath $OutZip -PathType Leaf) {
    $fi = Get-Item -LiteralPath $OutZip
    if ($fi.Length -eq $expectedSize -and (Sha256 $OutZip) -eq $expectedSha) {
      Write-Host "REUSE verified $name"
      return
    }
    Remove-Item -LiteralPath $OutZip -Force
  }

  $stem = [IO.Path]::GetFileNameWithoutExtension($name)
  $folder = Join-Path $Root $stem
  if (-not (Test-Path -LiteralPath $folder -PathType Container)) { throw "Missing parts folder: $folder" }

  $out = [IO.File]::Open($OutZip,[IO.FileMode]::Create,[IO.FileAccess]::Write,[IO.FileShare]::None)
  try {
    $parts = @($Archive.parts | Sort-Object {[int]$_.sequence})
    $n=0
    foreach ($part in $parts) {
      $n++
      $pp = Join-Path $folder ([string]$part.name)
      if (-not (Test-Path -LiteralPath $pp -PathType Leaf)) { throw "Missing part: $pp" }
      $fi = Get-Item -LiteralPath $pp
      if ($fi.Length -ne [int64]$part.size_bytes) { throw "Part size mismatch: $pp" }
      $ph = Sha256 $pp
      if ($ph -ne ([string]$part.sha256).ToLowerInvariant()) { throw "Part SHA256 mismatch: $pp" }
      $inp = [IO.File]::OpenRead($pp)
      try { $inp.CopyTo($out) } finally { $inp.Dispose() }
      if (($n % 10) -eq 0 -or $n -eq $parts.Count) { Write-Host "  $name parts $n/$($parts.Count)" }
    }
  } finally { $out.Dispose() }

  $z = Get-Item -LiteralPath $OutZip
  if ($z.Length -ne $expectedSize) { throw "Archive size mismatch $name $($z.Length) != $expectedSize" }
  $zh = Sha256 $OutZip
  if ($zh -ne $expectedSha) { throw "Archive SHA256 mismatch $name $zh" }
  Write-Host "ARCHIVE PASS $name $zh"
}

function Extract-ZipResumable([string]$ZipPath,[string]$Destination) {
  Add-Type -AssemblyName System.IO.Compression
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [IO.Directory]::CreateDirectory($Destination) | Out-Null
  $zip = [IO.Compression.ZipFile]::OpenRead($ZipPath)
  try {
    $i=0; $total=$zip.Entries.Count
    foreach ($entry in $zip.Entries) {
      if ([string]::IsNullOrEmpty($entry.Name)) { continue }
      $i++
      $rel = $entry.FullName.Replace('/',[IO.Path]::DirectorySeparatorChar)
      $target = Join-Path $Destination $rel
      $parent = Split-Path -Parent $target
      [IO.Directory]::CreateDirectory($parent) | Out-Null

      $needs = $true
      if (Test-Path -LiteralPath $target -PathType Leaf) {
        if ((Get-Item -LiteralPath $target).Length -eq [int64]$entry.Length) { $needs=$false }
      }
      if ($needs) {
        $partial = $target + ".restore_part"
        if (Test-Path -LiteralPath $partial) { Remove-Item -LiteralPath $partial -Force }
        $src=$entry.Open()
        $dst=[IO.File]::Open($partial,[IO.FileMode]::Create,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try { $src.CopyTo($dst) } finally { $dst.Dispose(); $src.Dispose() }
        if ((Get-Item -LiteralPath $partial).Length -ne [int64]$entry.Length) { throw "Extracted length mismatch: $($entry.FullName)" }
        Move-Item -LiteralPath $partial -Destination $target -Force
      }
      if (($i % 500) -eq 0 -or $i -eq $total) { Write-Host "  extract $i/$total from $([IO.Path]::GetFileName($ZipPath))" }
    }
  } finally { $zip.Dispose() }
}

function Resolve-Python {
  $py = Get-Command py -ErrorAction SilentlyContinue
  if ($py) { return @("py","-3") }
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) { return @("python") }
  throw "Python 3 not found. Install Python 3, then rerun this script."
}

Write-Host "=== L2-RESILIENCY-001 DRIVE RESTORE + 2025 VALIDATION V0.1B ==="
Write-Host "FROZEN V0.1B | 2025 ONLY | NO PNL / NO COSTS / NO SHARPE / NO 2026 / NO ORDERS"

[IO.Directory]::CreateDirectory($Base) | Out-Null
[IO.Directory]::CreateDirectory($RawRoot) | Out-Null
[IO.Directory]::CreateDirectory($EvidenceRoot) | Out-Null
[IO.Directory]::CreateDirectory($TmpRoot) | Out-Null

$rawFiles=@(Get-ChildItem -LiteralPath $RawRoot -Filter "BTC.lz4" -File -Recurse -ErrorAction SilentlyContinue)
$rawBytes=[int64]0
if ($rawFiles.Count -gt 0) { $rawBytes=[int64](($rawFiles | Measure-Object -Property Length -Sum).Sum) }
$needRestore = -not ($rawFiles.Count -eq $ExpectedObjects -and $rawBytes -eq $ExpectedBytes)

if ($needRestore) {
  Write-Host "RAW corpus absent/incomplete: count=$($rawFiles.Count) bytes=$rawBytes"
  $PartsRoot = Find-PartsRoot
  Write-Host "PartsRoot: $PartsRoot"
  $masterPath = Join-Path $PartsRoot $MasterName
  $master = Get-Content -LiteralPath $masterPath -Raw -Encoding UTF8 | ConvertFrom-Json

  foreach ($a in @($master.archives)) {
    $name=[string]$a.source_file
    if (-not $ExpectedArchives.ContainsKey($name)) { throw "Master contains unexpected archive: $name" }
    $e=$ExpectedArchives[$name]
    if ([int64]$a.source_size_bytes -ne [int64]$e.Size) { throw "Master archive size mismatch: $name" }
    if (([string]$a.source_sha256).ToLowerInvariant() -ne [string]$e.Sha) { throw "Master archive hash mismatch: $name" }

    $zipPath=Join-Path $TmpRoot $name
    Reassemble-Archive $a $PartsRoot $zipPath
    $RawArchiveRoot = Join-Path $RawRoot "market_data"
    Extract-ZipResumable $zipPath $RawArchiveRoot
    Remove-Item -LiteralPath $zipPath -Force
  }

  $rawFiles=@(Get-ChildItem -LiteralPath $RawRoot -Filter "BTC.lz4" -File -Recurse)
  $rawBytes=[int64](($rawFiles | Measure-Object -Property Length -Sum).Sum)
} else {
  Write-Host "REUSE existing full RAW corpus; Drive restore not required."
}

Write-Host "RAW SHAPE count=$($rawFiles.Count) bytes=$rawBytes"
if ($rawFiles.Count -ne $ExpectedObjects -or $rawBytes -ne $ExpectedBytes) {
  throw "FAIL CLOSED RAW corpus shape mismatch"
}
Write-Host "RAW CORPUS SHAPE PASS"

$python = Resolve-Python
$helper = Join-Path $PSScriptRoot "l2r_2025_rebuild_verified_manifest_v01a.py"
if (-not (Test-Path -LiteralPath $helper -PathType Leaf)) { throw "Missing helper: $helper" }

if ($python.Count -eq 2) { & $python[0] $python[1] $helper } else { & $python[0] $helper }
if ($LASTEXITCODE -ne 0) { throw "Manifest rebuild helper failed rc=$LASTEXITCODE" }

$manifestPath=Join-Path $EvidenceRoot "L2_RESILIENCY_001_2025_BTC_RAW_MANIFEST_V0_1.csv"
if ((Sha256 $manifestPath) -ne $ExpectedManifestSha) { throw "FAIL CLOSED frozen manifest SHA mismatch" }
Write-Host "MANIFEST PASS $ExpectedManifestSha"

$ExpectedRunnerSha = "e16efd7071a159fb767b6ff872f284e498ca110518bec06d9b4c3db867079a38"
$RunnerPayload = Join-Path $PSScriptRoot "L2R_2025_BTC_VALIDATION_PIPELINE_V01B_FROZEN_SOURCE.b64.txt"
$RunnerPath = Join-Path $TmpRoot "L2R_2025_BTC_VALIDATION_PIPELINE_V01B_FROZEN_SOURCE.py"
$EvidenceName = "L2_RESILIENCY_001_2025_VALIDATION_EVIDENCE_V0_1.zip"

if (-not (Test-Path -LiteralPath $RunnerPayload -PathType Leaf)) { throw "Missing frozen V0.1B runner payload: $RunnerPayload" }
$runnerB64 = (Get-Content -LiteralPath $RunnerPayload -Raw -Encoding ASCII) -replace "\s",""
[IO.File]::WriteAllBytes($RunnerPath,[Convert]::FromBase64String($runnerB64))
$runnerSha = Sha256 $RunnerPath
if ($runnerSha -ne $ExpectedRunnerSha) { throw "FAIL CLOSED V0.1B runner SHA mismatch: $runnerSha" }
Write-Host "V0.1B RUNNER PASS $runnerSha"

if ($python.Count -eq 2) {
  & $python[0] $python[1] -c "import lz4.frame, boto3"
} else {
  & $python[0] -c "import lz4.frame, boto3"
}
if ($LASTEXITCODE -ne 0) {
  Write-Host "Installing runtime-only Python dependencies lz4 + boto3..."
  if ($python.Count -eq 2) {
    & $python[0] $python[1] -m pip install --user "lz4==4.4.4" boto3
  } else {
    & $python[0] -m pip install --user "lz4==4.4.4" boto3
  }
  if ($LASTEXITCODE -ne 0) { throw "Could not install Python dependencies" }
}

Write-Host ""
Write-Host "============================================================"
Write-Host "EXECUTING FROZEN ONE-SHOT 2025 VALIDATION V0.1B"
Write-Host "OFFLINE EXISTING CORPUS: NO AWS / NO PAID REACQUISITION"
Write-Host "2026 FORBIDDEN | NO PNL | NO COSTS | NO SHARPE | NO LIVE TRADING"
Write-Host "NO POST-OUTCOME RETUNING"
Write-Host "============================================================"

if ($python.Count -eq 2) {
  & $python[0] $python[1] $RunnerPath --base $Base --workers 4 --offline-existing-corpus
} else {
  & $python[0] $RunnerPath --base $Base --workers 4 --offline-existing-corpus
}
$rc=$LASTEXITCODE
if ($rc -ne 0) { throw "V0.1B validation failed/blocked rc=$rc" }

$evidence=Join-Path $Base $EvidenceName
if (-not (Test-Path -LiteralPath $evidence -PathType Leaf)) { throw "Expected validation evidence bundle not produced: $evidence" }
$evSha=Sha256 $evidence
Write-Host "VALIDATION EVIDENCE PASS path=$evidence"
Write-Host "EVIDENCE_SHA256=$evSha"

$resultDir=$null
if (Test-PartsRoot $PartsRoot) {
  $resultDir=Join-Path $PartsRoot "_L2_VALIDATION_RESULTS"
} else {
  try {
    $detected=Find-PartsRoot
    $resultDir=Join-Path $detected "_L2_VALIDATION_RESULTS"
  } catch {
    $resultDir=Join-Path $Base "_L2_VALIDATION_RESULTS_LOCAL"
  }
}
[IO.Directory]::CreateDirectory($resultDir) | Out-Null
$dest=Join-Path $resultDir $EvidenceName
Copy-Item -LiteralPath $evidence -Destination $dest -Force

$receiptPath=Join-Path $EvidenceRoot "L2_RESILIENCY_001_VALIDATION_2025_RECEIPT_V0_1.json"
if (Test-Path -LiteralPath $receiptPath -PathType Leaf) {
  Copy-Item -LiteralPath $receiptPath -Destination (Join-Path $resultDir ([IO.Path]::GetFileName($receiptPath))) -Force
}

$status=[ordered]@{
  schema_version="0.1B"
  lab_id=$LabId
  classification="FROZEN_2025_VALIDATION_EXECUTED"
  evidence_sha256=$evSha
  raw_objects=$ExpectedObjects
  raw_bytes=$ExpectedBytes
  manifest_sha256=$ExpectedManifestSha
  runner_sha256=$ExpectedRunnerSha
  copied_result=$dest
  access_2026=$false
  pnl_computed=$false
  costs_computed=$false
  sharpe_computed=$false
  live_trading=$false
  orders=$false
  exchange_mutation=$false
}
$status | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $resultDir "L2R_2025_VALIDATION_V01B_LOCAL_EXECUTION_RECEIPT.json") -Encoding UTF8
Write-Host "COPIED VALIDATION RESULT: $dest"
Write-Host "=== V0.1B COMPLETE ==="
