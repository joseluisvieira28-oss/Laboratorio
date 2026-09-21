# CED1D-0031 V0.2B — GITHUB RUNNER SOURCE BLOCK RECEIPT — 2026-09-21

Status: **SOURCE_BLOCKED_GITHUB_RUNNER_REGION**

Candidate identity remains: CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1.

## Evidence

- Original scheduled run: 35546300715.
- Original failure: Binance Vision daily AVAXUSDT 1m file for 2026-09-20 was not yet published at the scheduled attempt.
- Authorized rerun job: 106455030819.
- Rerun progressed after the daily file became available, then failed closed because the collector used an invalid futures funding transport on data-api.binance.vision.
- Remediation PR: #38.
- V0.2B QA run: 35637744671.
- Synthetic identity QA: PASS.
- Correct documented USD-M funding endpoint probed: https://fapi.binance.com/fapi/v1/fundingRate
- GitHub-hosted runner response: **HTTP 451**.
- No authenticated API, API key, account, wallet, order, exchange mutation, PnL or live capital was used.

## Decision

Do not activate V0.2B on the GitHub-hosted runner.
Do not use a proxy/VPN or other geoblock bypass.
Do not substitute another venue or synthetic funding source.
Do not backfill the missed 2026-09-18..2026-09-20 forward paths.
The 2026-09-21 MICRO-LIVE decision remains NO-GO.

The candidate is not NO_EDGE. The collector is SOURCE_BLOCKED in the current GitHub runner geography.

## Smallest future safe options

1. Use an explicitly authorized European research runtime that can access the same official public Binance USD-M endpoint, with prospective boundary reset before any new admitted outcomes; or
2. Wait for a defensible official Binance archival funding source with timing compatible with the frozen forward protocol.

No scientific rule change is authorized by this receipt.
