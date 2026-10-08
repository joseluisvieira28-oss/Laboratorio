# Triple V0.3 — exit 1 / heartbeat audit — 2026-10-08

Status: PARTIAL_VERIFIED; exact local cause UNPROVEN.
Scope: static source and GitHub CI reads; no runtime execution, account access, orders, arming, deployment or main merge.
Parent audit: 44686f8269d6fceae0463b5701ce9663d3d95400.
Operator source inspected: a4539225674e0765eb5a5cb664b6cfbe43b6ba7d (PR #160, open draft).
Local observations are operator-provided, not remotely verified.

## Findings

1. Scheduled-task Ready means not running, not trading readiness. The installer defines only AtLogOn, 10 one-minute retries and IgnoreNew. Empty NextRunTime is consistent with an event trigger. Exhausted retries do not create indefinite recovery. No task XML/principal evidence establishes which identity ran the task or whether it changed.
2. LastRunTime 2026-10-02 14:13:44 and supervisor file mtime 2026-10-05 19:20:49Z cannot yet be assigned to the same invocation. LastRunTime timezone was not independently established. A manual launch, another task/writer, copied file or task replacement remains possible. Obtain embedded checked_at_utc and clock context. File mtime alone is not a process heartbeat.
3. Runner preflight creates runtime directories, then requires main EXE, overlay EXE, correction catalog AND historical_options_receipts. The previous local inventory covered executable/script files; it does NOT prove the catalog or archive is absent.
4. Overlay executes before DPAPI loading and outside the try/finally block. It returns 2 for invalid/missing/duplicate historical reconciliation, stored-PnL mismatch, missing fill or mismatched entry/exit order identities. Runner converts any nonzero overlay exit into an unhandled throw: powershell.exe -File may then report 1. Therefore task code 1 need not be the child process code. Overlay output is not persisted by the runner. Output-writing failures can also escape the overlay's validation catch.
5. Missing DPAPI files, wrong Windows identity/profile, undecryptable cipher or read permissions can terminate before main launch. Do not decrypt, display or copy secrets in this audit. ARMED=false does not bypass DPAPI loading.
6. Main child exit is propagated with exit LASTEXITCODE. Constructors load local databases/state before the loop; invalid JSON, SQLite failures, filesystem permissions, disk issues or executable bootstrap errors are possible fatal causes. run_forever has no outer exception handler. Source poll errors, manage_active errors and enter_signal errors are caught and recorded; those caught failures alone should not stop heartbeat. Exceptions from arbitration, mark, JSON serialization or atomic state replacement can escape. No fatal traceback is currently available.
7. Runner has no transcript, stdout/stderr redirection or structured launcher failure receipt. Disabled TaskScheduler Operational logging removes that source of historical evidence; an empty filtered Application-log result does not exclude a normal Python/PowerShell failure. PyInstaller failure need not be a Windows crash.
8. No process currently observed supports that the supervisor is stopped at observation time, rather than merely hung, assuming process inspection is complete. Why it stopped remains unproven.
9. ARMED=false is a current local marker observation, not historical authority proof. GlobalSlot=false does not prove absence of exchange positions/orders/TP-SL. An unarmed engine may still manage locally owned positions. Never run the launcher, installer, readiness/arm or switch scripts as a diagnostic shortcut.

## Binary provenance and actual CI

Build https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/36722620249:
completed/success, head e581823ae82c6c14ab9ae9d984430ba6e248a9ea.
Job 109911331357 logs independently show 6 synthetic probes with zero failures,
82 regressions passing (not merely the earlier summary of 74), EXE --help smoke,
packaging and hashes. This validates the built candidate, not the installed HOTFIX2 package.
Release audit https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/36722713131:
completed/success, head 6e216b30e5e063a4ed63cec78bad20886280c490.
Current artifact listing for the build is empty; receipt advertises expiry 2026-10-07T13:40:03Z.
Artifact expiry affects retrieval, not execution of a downloaded EXE.
Parent audit commit has zero workflow runs in the queried head_sha endpoint; no tests were rerun here.

| File | Operator local bytes | Validated build bytes | Validated SHA256 |
|---|---:|---:|---|
| MEXCTripleFishingOperatorV03.exe | 15022774 | 15021048 | 3fc834c2a26514861cfd51ae3ff47776c49042748baf4a969b1639c06c68af35 |
| BuildOptionsCorrectionOverlayV01.exe | 8324938 | 8326411 | 4e2827ac12b3faba5e049cbb94df3389c59acb108ae29510cd33b5b655110291 |
| MEXCTripleFishingReadyV03.exe | 8943352 | 8943352 | aa47f4ed3e009d20c4bfbada458ccb2b03a6b74a6ad2d2a857c84c0e4a98d733 |
| Run_MEXC_Triple_Fishing_V03.ps1 | 3667 | 3667 | e46df211b477ef809139ae262c34ae1b783fcead7cef34b03658b2a7f83a60c3 |

Main and overlay cannot be byte-identical to that validated build given their different lengths.
This proves a package provenance discrepancy, not which older source they contain or why they fail.
Same Ready length does not prove hash identity. Dates are not version proof.
The freshness hotfix changes readiness time comparison; it does not restart the supervisor.
Verify local hashes, BUILD_INFO and actual Run contents before assuming source matches.
References:
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/a4539225674e0765eb5a5cb664b6cfbe43b6ba7d/crypto_edge_radar/windows/Run_MEXC_Triple_Fishing_V03.ps1
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/a4539225674e0765eb5a5cb664b6cfbe43b6ba7d/crypto_edge_radar/windows/Install_MEXC_Triple_Fishing_V03.ps1
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/a4539225674e0765eb5a5cb664b6cfbe43b6ba7d/crypto_edge_radar/scripts/mexc_triple_fishing_operator_v03.py
- https://github.com/joseluisvieira28-oss/Laboratorio/blob/a4539225674e0765eb5a5cb664b6cfbe43b6ba7d/crypto_edge_radar/scripts/build_options_v21_pnl_correction_overlay_v01.py

## Safe corrections, pending evidence

Preserve existing state, immutable receipts, slot and markers. Do not remove blockers or manufacture a passing overlay.
First capture hashes and nonsecret launcher/task/state metadata.
A future code change should add bounded structured launcher stage records and numeric child exit codes;
never persist credentials, environment dumps, arbitrary exception text, raw account replies or complete transcripts without sanitization.
Fatal supervisor exceptions need a sanitized local diagnostic receipt and nonzero exit, preserving slot/receipts.
Test missing catalog/archive, overlay failure, unavailable DPAPI and main failure using temporary files and inert stub executables only.
Do not add automatic restart triggers: startup can manage positions and requires independently confirmed exchange state.
Do not replace binaries yet; establish hashes and build provenance, then review a coherent fresh package separately.
No runtime correction is deployed or claimed fixed by this document.

## Operator-only read-only collection (stage 1)

Run in the existing operator PowerShell session. Does not launch a bundle executable or decrypt secrets.
Share the output; do not share secret files, environment values or raw logs.
If a field has unexpected private text, redact it first.

```powershell
$bundleAudit = 'C:\Users\José\Desktop\MEXC_TRIPLE_FISHING_V03_HOTFIX2'
$runtimeAudit = Join-Path $env:LOCALAPPDATA 'CryptoLab\TripleFishingV03'
$taskAudit = Get-ScheduledTask -TaskName 'CryptoLab-Triple-Fishing-Operator-V03'
Get-Date -Format o
Get-TimeZone | Select-Object Id
$taskAudit.Principal | Select-Object UserId,LogonType,RunLevel
$taskAudit.Actions | Select-Object Execute,Arguments,WorkingDirectory
$taskAudit.Triggers | Select-Object @{n='Type';e={$_.CimClass.CimClassName}},Enabled,StartBoundary,EndBoundary,UserId,Delay,Repetition
$taskAudit.Settings | Select-Object Enabled,RestartCount,RestartInterval,MultipleInstances,ExecutionTimeLimit
Get-ScheduledTaskInfo -InputObject $taskAudit | Select-Object LastRunTime,LastTaskResult,NextRunTime,NumberOfMissedRuns

foreach ($nameAudit in @('Run_MEXC_Triple_Fishing_V03.ps1','MEXCTripleFishingOperatorV03.exe','MEXCTripleFishingReadyV03.exe','BuildOptionsCorrectionOverlayV01.exe','OPTIONS_V21_HISTORICAL_FEE_CORRECTION_CATALOG_V01.json','BUILD_INFO.json','SHA256SUMS.txt')) {
    $pathAudit = Join-Path $bundleAudit $nameAudit
    if (Test-Path -LiteralPath $pathAudit -PathType Leaf) {
        $itemAudit = Get-Item -LiteralPath $pathAudit
        [pscustomobject]@{Name=$nameAudit;Length=$itemAudit.Length;LastWriteTimeUtc=$itemAudit.LastWriteTimeUtc;SHA256=(Get-FileHash -LiteralPath $pathAudit -Algorithm SHA256).Hash}
    } else { [pscustomobject]@{Name=$nameAudit;Missing=$true} }
}
$archiveAudit = Join-Path $runtimeAudit 'historical_options_receipts'
[pscustomobject]@{
    ArchiveExists=(Test-Path -LiteralPath $archiveAudit -PathType Container)
    ReconciliationCount=@(Get-ChildItem -LiteralPath $archiveAudit -Filter 'POST_TRADE_RECONCILIATION.json' -Recurse -File -ErrorAction SilentlyContinue).Count
    KeyFileExists=(Test-Path -LiteralPath (Join-Path $env:LOCALAPPDATA 'CryptoEdgeRadar\secrets\mexc_api_key.dpapi') -PathType Leaf)
    SecretFileExists=(Test-Path -LiteralPath (Join-Path $env:LOCALAPPDATA 'CryptoEdgeRadar\secrets\mexc_api_secret.dpapi') -PathType Leaf)
}
$stateAudit = Join-Path $runtimeAudit 'live_state\triple_fishing_operator_v03.json'
if (Test-Path -LiteralPath $stateAudit -PathType Leaf) {
    Get-Item -LiteralPath $stateAudit | Select-Object Length,LastWriteTimeUtc
    try {
        $jsonAudit = Get-Content -LiteralPath $stateAudit -Raw | ConvertFrom-Json -ErrorAction Stop
        $jsonAudit | Select-Object version,status,checked_at_utc,pending_signal_count
        $jsonAudit.engine | Select-Object status
        $jsonAudit.source_state.PSObject.Properties | ForEach-Object {
            [pscustomobject]@{Lane=$_.Name;Status=$_.Value.status}
        }
    } catch { Write-Output 'STATE_JSON_READ_OR_PARSE_FAILED (details withheld)' }
}
foreach ($rootAudit in @($bundleAudit,$runtimeAudit)) {
    Get-ChildItem -LiteralPath $rootAudit -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in '.log','.err','.out','.txt' } |
        Sort-Object LastWriteTimeUtc -Descending |
        Select-Object -First 20 FullName,Length,LastWriteTimeUtc
}
```

If Run hash matches, remote source already supplies its contents. If it differs, obtain a locally reviewed/redacted script copy; do not execute it.
Subsequent log excerpts must be selected and scrubbed only after paths are known.
A generic DPAPI check under this interactive identity cannot prove access under the task principal.
Account read-only confirmation remains a separate independent prerequisite for any restart/arming, outside this audit's authorization.
