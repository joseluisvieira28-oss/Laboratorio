# OPTIONS-SPOTPERP-001 — V0.1

Status: **FROZEN / QUEUED / SOURCE AUDIT ONLY**

This branch prepares the source/provenance audit for the first Options → Spot/Perp MVE.
It does **not** run Discovery, compute skew values, forward returns, PnL, inspect 2025,
inspect 2026, place orders, or mutate any exchange state.

The sole active frontier remains `ONCHAIN-CAPFLOW-001` until its current gate is resolved.

## Frozen authority

Google Drive:
`OPTIONS-SPOTPERP-001 — QUEUED PRE-DISCOVERY PROTOCOL — V0.1`

Drive ID:
`1RtBYsET0t8yFAVDCJV1mEmGCAikMp-UQS0Yd802blBc`

Canonical authority SHA256:
`138cee737d75d27b43d9f377fc9a77e823e8fb2015f360b300cdc4a16cf67cfa`

## Frozen primary source

Deribit public historical BTC option trades:
`https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time`

The frozen Source/Data Audit covers only `2021-04-01` through `2024-12-31` UTC and
must never request or inspect 2025/2026.

## Final source/data gate

`source_audit.py` performs the incremental Deribit acquisition and coverage audit.
`source_audit_gate.py` is the authoritative final PASS wrapper. It re-validates the raw
responses and adds fail-closed checks that are required by the Drive protocol:

- actual machine-protocol binding to the frozen Drive authority;
- SHA256 verification of every saved Deribit raw page;
- required `trade_id` presence and exact duplicate detection;
- timestamp monotonicity within retrieval pages;
- each trade timestamp constrained to its explicit request interval and to the frozen Discovery window;
- canonical BTC option instrument parsing;
- finite positive IV, index price and mark price;
- `buy`/`sell` direction validation;
- positive finite trade amount when present;
- preservation of the frozen 30–120 DTE and OTM call/put coverage gate from `source_audit.py`;
- at least 500 valid source-coverage days;
- official Binance Vision BTCUSDT Spot 1d archives for Apr-2021 through Dec-2024 only;
- exactly 45 monthly BTC archives;
- exact daily cutoff `2021-04-01` through `2024-12-31` with no missing/duplicate dates and no 2025+ timestamps;
- SHA256 provenance for each BTC archive.

The final receipt is:
`source_audit_data/source_gate_receipt.json`

The final gate explicitly computes **NO SKEW, NO SIGNAL, NO FORWARD RETURN and NO PnL**.

## Outcome-blind preflight — PASS — 2026-09-13

A static GitHub Actions preflight was completed before any Options market-data acquisition.

- Workflow: `.github/workflows/options-source-audit-preflight-v01.yml`
- Run ID: `34768087260`
- Job ID: `103752569614`
- Head SHA: `2f0107b1549d69b246d505e82ec47d7858f47e0c`
- Verdict: `OPTIONS_SOURCE_AUDIT_PREFLIGHT_PASS`

The logs explicitly state:
`NO NETWORK | NO MARKET DATA | NO SKEW | NO RETURNS | NO PNL`
and
`2025 LOCKED / 2026 LOCKED`.

This PASS validates implementation/preflight only. It is **not** a Source Audit PASS,
Discovery PASS, or trading-edge result.

## Implementation hardening — 2026-09-13

Before the first full source-audit execution, the implementation was hardened without
changing the frozen research hypothesis:

- DNS, timeout and transport failures return `EXECUTION_ENVIRONMENT_BLOCKED` with exit code `12`, never a false scientific source verdict;
- failures write structured partial receipts instead of dying with an unclassified traceback;
- trade rows are processed incrementally rather than retained for the whole 2021–2024 period;
- exact duplicate trade-ID detection uses local temporary SQLite work tables;
- HTTP 429 handling respects `Retry-After` when supplied;
- raw response pages remain gzip-compressed and SHA256-bound;
- 2025/2026 request construction remains fail-closed;
- the Windows runner now routes through `source_audit_gate.py`, so the stricter final gate controls PASS.

No skew rule, DTE bucket, moneyness bucket, minimum instrument count, minimum coverage
requirement, Discovery period, cost assumption, outcome horizon, or holdout rule changed.

## Windows — only after governance releases Priority #2

From this folder:

`run_source_audit_windows.bat`

That command now executes the **final** Source/Data Audit gate.

A limited probe, if specifically authorized, can be run with:

`python source_audit_gate.py --probe-days 3 --output .\source_audit_probe`

A probe can never return `SOURCE_AUDIT_PASS`.

Possible terminal states:
- `SOURCE_AUDIT_PASS` — source/data route is adequate for the frozen MVE;
- `SOURCE_AUDIT_BLOCKED` — source/provenance/schema/coverage/cutoff gate failed;
- `EXECUTION_ENVIRONMENT_BLOCKED` — DNS/network/transport problem only; not a scientific verdict;
- `PROBE_ONLY_NO_DECISION` — limited probe only; cannot authorize Discovery.

## Governance gate

Actual Options source-data acquisition remains blocked while `ONCHAIN-CAPFLOW-001` is the
active frontier. Only after that frontier reaches the relevant governance gate may this
queued Source/Data Audit be executed.

Only `SOURCE_AUDIT_PASS`, plus formal activation of Priority #2, can authorize creation of an
Options Discovery runner. No Options Discovery code is included in V0.1.

2025 remains locked until the frozen Options MVE-0 passes and its Discovery closeout is
written first. 2026 remains locked under V0.1.
