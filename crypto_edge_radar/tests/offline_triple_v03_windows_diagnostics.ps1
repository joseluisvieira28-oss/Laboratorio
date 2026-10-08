$ErrorActionPreference = "Stop"

# Offline smoke/negative-case tests only. NEVER invoke operator, overlay,
# installer, readiness/arm, switch, account, private API or exchange endpoints.
$repo = Split-Path -Parent $PSScriptRoot
$windows = Join-Path $repo "windows"
$runner = Join-Path $windows "Run_MEXC_Triple_Fishing_V03.ps1"
$watcher = Join-Path $windows "Watch_MEXC_Triple_Fishing_V03_ReadOnly.ps1"

foreach ($file in @($runner, $watcher)) {
    $tokens = $null
    $errors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($file, [ref]$tokens, [ref]$errors)
    if ($errors.Count -ne 0) {
        throw "PowerShell parse failed: $([IO.Path]::GetFileName($file))"
    }
}
Write-Host "PASS: both PowerShell diagnostics scripts parse"

$runnerSource = Get-Content -LiteralPath $runner -Raw
foreach ($required in @("REQUIREMENTS","OVERLAY","DPAPI","ENVIRONMENT","MAIN","MAIN_RETURNED","TRIPLE_V03_LAUNCH_DIAGNOSTIC_V01")) {
    if (-not $runnerSource.Contains($required)) {
        throw "Missing launcher stage/schema: $required"
    }
}
if ($runnerSource -match 'Write-TripleLaunchReceipt[^\r\n]*\$_') {
    throw "Unsafe arbitrary exception interpolation in launcher receipt"
}
Write-Host "PASS: six fixed launcher stages and fixed receipt schema"

$runtime = Join-Path ([IO.Path]::GetTempPath()) ("triple-v03-watch-test-" + [guid]::NewGuid().ToString("N"))
try {
    New-Item -ItemType Directory -Force -Path (Join-Path $runtime "live_state") | Out-Null
    $taskName = "CryptoLab-Offline-Fake-Nonexistent-Task-V03"
    $missing = (& $watcher -RuntimeRoot $runtime -TaskName $taskName | ConvertFrom-Json)
    if ($missing.heartbeat -ne "MISSING" -or $missing.health -ne "UNHEALTHY_HEARTBEAT") {
        throw "Missing heartbeat did not fail closed"
    }
    Write-Host "PASS: missing heartbeat fails closed"

    $state = Join-Path $runtime "live_state\triple_fishing_operator_v03.json"
    Set-Content -LiteralPath $state -Encoding UTF8 -Value '{"version":"TRIPLE_FISHING_OPERATOR_V0.3","checked_at_utc":"2000-01-01T00:00:00Z","status":"WATCHING_THREE_LANES"}'
    $stale = (& $watcher -RuntimeRoot $runtime -TaskName $taskName | ConvertFrom-Json)
    if ($stale.heartbeat -ne "STALE" -or $stale.exchange_positions_verified) {
        throw "Stale heartbeat was not classified read-only and fail closed"
    }
    Write-Host "PASS: stale heartbeat fails closed"

    Set-Content -LiteralPath $state -Encoding UTF8 -Value "{"
    $corrupt = (& $watcher -RuntimeRoot $runtime -TaskName $taskName | ConvertFrom-Json)
    if ($corrupt.heartbeat -ne "MALFORMED" -or $corrupt.trade_authority_verified) {
        throw "Corrupt state was not classified fail closed"
    }
    Write-Host "PASS: malformed heartbeat fails closed"

    $future = ([DateTimeOffset]::UtcNow.AddMinutes(10)).ToString("o")
    $stateBody = @{ version="TRIPLE_FISHING_OPERATOR_V0.3"; checked_at_utc=$future; status="WATCHING_THREE_LANES" } | ConvertTo-Json -Compress
    Set-Content -LiteralPath $state -Encoding UTF8 -Value $stateBody
    $clockBad = (& $watcher -RuntimeRoot $runtime -TaskName $taskName | ConvertFrom-Json)
    if ($clockBad.heartbeat -ne "CLOCK_MISMATCH") {
        throw "Future heartbeat not rejected"
    }
    Write-Host "PASS: future heartbeat fails closed"

    $fresh = ([DateTimeOffset]::UtcNow).ToString("o")
    $stateBody = @{ version="TRIPLE_FISHING_OPERATOR_V0.3"; checked_at_utc=$fresh; status="WATCHING_THREE_LANES" } | ConvertTo-Json -Compress
    Set-Content -LiteralPath $state -Encoding UTF8 -Value $stateBody
    $unarmed = (& $watcher -RuntimeRoot $runtime -TaskName $taskName | ConvertFrom-Json)
    if ($unarmed.heartbeat -ne "FRESH" -or $unarmed.armed_marker_present -or $unarmed.trade_authority_verified) {
        throw "Fresh local heartbeat fabricated live authority"
    }
    Write-Host "PASS: fresh heartbeat does not fabricate trade authority"

    if ((Get-ChildItem -LiteralPath $runtime -Recurse -File).Count -ne 1) {
        throw "Read-only watcher unexpectedly created files"
    }
    Write-Host "PASS: watcher did not mutate audit fixture"
} finally {
    Remove-Item -LiteralPath $runtime -Force -Recurse -ErrorAction SilentlyContinue
}
Write-Host "ALL OFFLINE WINDOWS DIAGNOSTIC TESTS PASS"
