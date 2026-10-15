# Verifies this package only. Does not touch existing tasks/data/credentials.
$ErrorActionPreference='Stop'
$manifest=Get-Content (Join-Path $PSScriptRoot 'BUILD_MANIFEST.json') -Raw | ConvertFrom-Json
foreach ($f in $manifest.files) {
    if ([IO.Path]::GetFileName($f.name) -ne $f.name) {throw 'BAD_MANIFEST_FILENAME'}
    $p=Join-Path $PSScriptRoot $f.name
    $actual=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $f.sha256) {throw "HASH_MISMATCH: $($f.name)"}
}
foreach ($v in @('07','11')) {
    & (Join-Path $PSScriptRoot "V${v}_AUDIT_PREVIEW.exe") --self-test
    if ($LASTEXITCODE -ne 0) {throw 'OFFLINE_SELFTEST_FAILED'}
}
Write-Output ('SOURCE_COMMIT: '+$manifest.source_commit)
Write-Output 'PACKAGE_VERIFIED_OFFLINE; EXISTING_TASKS_UNCHANGED; NO_REAL_TELEGRAM_SEND'
