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

  throw "Could not locate $MasterName. Mount Google Drive for Desktop or rerun with -PartsRoot 'X:\path\L2R_2025_DRIVE_PARTS_220MiB'."
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

Write-Host "=== L2-RESILIENCY-001 DRIVE RESTORE + SOURCE CLOCK V0.1A ==="
Write-Host "NO SWEEPS / NO RETURNS / NO PNL / NO 2026 / NO ORDERS"

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
    Extract-ZipResumable $zipPath $RawRoot
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

$pkgPath=Join-Path $TmpRoot "L2R_2025_BTC_SOURCE_CLOCK_DIAGNOSTIC_V01A.zip"
$pkgDir=Join-Path $TmpRoot "SOURCE_CLOCK_V01A"
$pkgB64=@'
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
'@
[IO.File]::WriteAllBytes($pkgPath,[Convert]::FromBase64String(($pkgB64 -replace "\s","")))
if ((Sha256 $pkgPath) -ne $ExpectedPackageSha) { throw "FAIL CLOSED diagnostic package hash mismatch" }

if (Test-Path -LiteralPath $pkgDir) { Remove-Item -LiteralPath $pkgDir -Recurse -Force }
[IO.Directory]::CreateDirectory($pkgDir) | Out-Null
[IO.Compression.ZipFile]::ExtractToDirectory($pkgPath,$pkgDir)

foreach ($member in $ExpectedMembers.Keys) {
  $mp=Join-Path $pkgDir $member
  if (-not (Test-Path -LiteralPath $mp -PathType Leaf)) { throw "Package member missing: $member" }
  $mh=Sha256 $mp
  if ($mh -ne $ExpectedMembers[$member]) { throw "Package member SHA mismatch: $member" }
}
Write-Host "V0.1A PACKAGE + MEMBERS PASS"

if ($python.Count -eq 2) { & $python[0] $python[1] -c "import lz4.frame" } else { & $python[0] -c "import lz4.frame" }
if ($LASTEXITCODE -ne 0) {
  Write-Host "Installing lz4 Python dependency..."
  if ($python.Count -eq 2) { & $python[0] $python[1] -m pip install --user "lz4==4.4.4" } else { & $python[0] -m pip install --user "lz4==4.4.4" }
  if ($LASTEXITCODE -ne 0) { throw "Could not install lz4" }
}

Write-Host "RUNNING FROZEN FULL-CORPUS SOURCE-CLOCK V0.1A..."
Push-Location $pkgDir
try {
  & cmd.exe /d /c "RUN_2025_SOURCE_CLOCK_DIAGNOSTIC_V01A.bat"
  $rc=$LASTEXITCODE
} finally { Pop-Location }
if ($rc -ne 0) { throw "V0.1A diagnostic failed rc=$rc" }

$evidence=Join-Path $Base "L2_RESILIENCY_001_2025_SOURCE_CLOCK_DIAGNOSTIC_EVIDENCE_V0_1.zip"
if (-not (Test-Path -LiteralPath $evidence -PathType Leaf)) { throw "Expected evidence bundle not produced: $evidence" }
$evSha=Sha256 $evidence
Write-Host "EVIDENCE PASS path=$evidence"
Write-Host "EVIDENCE_SHA256=$evSha"

$resultDir=$null
if (Test-PartsRoot $PartsRoot) {
  $resultDir=Join-Path $PartsRoot "_L2_DIAGNOSTIC_RESULTS"
} else {
  try {
    $detected=Find-PartsRoot
    $resultDir=Join-Path $detected "_L2_DIAGNOSTIC_RESULTS"
  } catch {
    $resultDir=Join-Path $Base "_L2_DIAGNOSTIC_RESULTS_LOCAL"
  }
}
[IO.Directory]::CreateDirectory($resultDir) | Out-Null
$dest=Join-Path $resultDir ([IO.Path]::GetFileName($evidence))
Copy-Item -LiteralPath $evidence -Destination $dest -Force
$status=[ordered]@{
  schema_version="0.1A"
  lab_id=$LabId
  classification="SOURCE_CLOCK_DIAGNOSTIC_EXECUTED"
  evidence_sha256=$evSha
  raw_objects=$ExpectedObjects
  raw_bytes=$ExpectedBytes
  manifest_sha256=$ExpectedManifestSha
  diagnostic_package_sha256=$ExpectedPackageSha
  copied_result=$dest
  sweeps_computed=$false
  returns_computed=$false
  pnl_computed=$false
  access_2026=$false
}
$status | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $resultDir "L2R_2025_SOURCE_CLOCK_V01A_LOCAL_EXECUTION_RECEIPT.json") -Encoding UTF8
Write-Host "COPIED EVIDENCE RESULT: $dest"
Write-Host "=== COMPLETE ==="
