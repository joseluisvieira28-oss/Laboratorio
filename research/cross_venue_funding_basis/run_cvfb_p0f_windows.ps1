$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $RepoRoot

Write-Host "CVFB P0F Windows runner - source-only / requester-pays / fail-closed"
Write-Host "No credential value will be printed or written by this wrapper."

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python was not found on PATH."
}

python -c "import importlib,sys; mods=['boto3','lz4.frame','msgpack']; missing=[]; [missing.append(m) for m in mods if importlib.util.find_spec(m.split('.')[0]) is None]; print('P0F_PYTHON_DEPENDENCIES_PRESENT' if not missing else 'MISSING_PYTHON_DEPENDENCIES '+','.join(missing)); sys.exit(0 if not missing else 2)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Install the frozen runtime first:"
    Write-Host "python -m pip install -r research/cross_venue_funding_basis/requirements_p0e_v01.txt"
    exit $LASTEXITCODE
}

python -c "import boto3,sys; c=boto3.Session().get_credentials(); ok=c is not None and bool(c.get_frozen_credentials().access_key) and bool(c.get_frozen_credentials().secret_key); print('P0F_AWS_CREDENTIAL_PROVIDER_READY' if ok else 'P0F_AWS_CREDENTIALS_ABSENT_OR_INCOMPLETE'); sys.exit(0 if ok else 3)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Configure AWS credentials through a standard boto3 provider."
    Write-Host "Do NOT paste credentials into this script or commit them to Git."
    exit $LASTEXITCODE
}

$env:CVFB_P0F_EXPLORER_BLOCKS_REQUESTER_PAYS_AUTHORIZED = "YES"
$outDir = Join-Path $RepoRoot "out\cvfb_p0f"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$outFile = Join-Path $outDir "CVFB_NATIVE_ORACLE_PROVENANCE_P0F_RECEIPT_V0.1A.json"

python research/cross_venue_funding_basis/cvfb_native_oracle_p0f_explorer_blocks_v01a.py --execute --authorization-confirmation "I_EXPLICITLY_AUTHORIZE_CVFB_P0F_EXPLORER_BLOCKS_REQUESTER_PAYS" --out $outFile
$rc = $LASTEXITCODE

Remove-Item Env:CVFB_P0F_EXPLORER_BLOCKS_REQUESTER_PAYS_AUTHORIZED -ErrorAction SilentlyContinue

if ($rc -ne 0) {
    Write-Host "P0F did not complete. Exit code: $rc"
    exit $rc
}

python -c "import json; x=json.load(open(r'$outFile',encoding='utf-8')); print('P0F_DECISION',x.get('decision')); assert x.get('economic_outcomes_computed') is False; assert x.get('2026_opened') is False; assert x.get('raw_object_bodies_emitted') is False"
if ($LASTEXITCODE -ne 0) {
    throw "P0F receipt firewall verification failed."
}

Write-Host "P0F receipt written to:"
Write-Host $outFile
