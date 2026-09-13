# OPTIONS-SPOTPERP-001 — V0.1

Status: **FROZEN / QUEUED / SOURCE AUDIT ONLY**

This branch prepares the source/provenance audit for the first Options → Spot/Perp MVE.
It does **not** run Discovery, compute forward returns, compute PnL, inspect 2025, inspect
2026, place orders, or mutate any exchange state.

## Frozen authority

Google Drive:
`OPTIONS-SPOTPERP-001 — QUEUED PRE-DISCOVERY PROTOCOL — V0.1`

Drive ID:
`1RtBYsET0t8yFAVDCJV1mEmGCAikMp-UQS0Yd802blBc`

Canonical authority SHA256:
`138cee737d75d27b43d9f377fc9a77e823e8fb2015f360b300cdc4a16cf67cfa`

## Source-audit purpose

Verify that Deribit public historical BTC option trades can support the frozen
trade-implied skew signal with adequate 2021-04-01 through 2024-12-31 coverage,
without opening any outcome data.

Primary source:
`https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time`

The audit checks:
- explicit date cutoffs;
- no 2025+ timestamps;
- trade-ID duplicates;
- instrument parsing;
- transaction IV and index-price presence;
- 30–120 day DTE eligibility;
- frozen OTM call/put moneyness buckets;
- at least 5 distinct eligible instruments per side;
- at least 500 valid signal-coverage days;
- SHA256 hashes of saved raw responses.

It explicitly does **not** calculate skew values, forward returns, PnL, Sharpe,
or any trading outcome metric.

## Implementation hardening — 2026-09-13

Before the first full local source-audit execution, the implementation was hardened without changing the frozen research hypothesis:
- DNS, timeout and transport failures now return `EXECUTION_ENVIRONMENT_BLOCKED` with exit code `12`, never a false scientific source verdict;
- failures write structured partial `source_manifest.json` and `source_audit_report.json` receipts instead of dying with an unclassified traceback;
- trade rows are processed incrementally rather than retained for the whole 2021–2024 period;
- exact duplicate trade-ID detection uses a temporary local SQLite work table, reducing RAM pressure while preserving exact duplicate checks;
- HTTP 429 handling respects `Retry-After` when supplied;
- raw response pages remain gzip-compressed and SHA256-bound;
- 2025/2026 request construction remains fail-closed.

No skew rule, DTE bucket, moneyness bucket, minimum instrument count, minimum coverage requirement, Discovery period, cost assumption, or holdout rule changed.

## Windows

From this folder:

`run_source_audit_windows.bat`

Optional connectivity/schema probe only:

`python source_audit.py --probe-days 3 --output .\source_audit_probe`

A probe can never return `SOURCE_AUDIT_PASS`.

Possible terminal states:
- `SOURCE_AUDIT_PASS` — source route is adequate for the frozen MVE;
- `SOURCE_AUDIT_BLOCKED` — source/provenance/coverage gate failed;
- `EXECUTION_ENVIRONMENT_BLOCKED` — local DNS/network/transport problem only; re-run unchanged after connectivity is restored;
- `PROBE_ONLY_NO_DECISION` — limited probe only; cannot authorize Discovery.

## Gate

Only `SOURCE_AUDIT_PASS`, plus the project governance decision that
ONCHAIN-CAPFLOW-001 has reached its gate, can authorize creation of a Discovery runner.

No Discovery code is included in V0.1.
