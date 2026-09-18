# DEFI-LIQUIDATION-SHOCK-001 — FIRST-SUCCESS BOUNDARY IMPLEMENTATION FREEZE V0.1

Date: 2026-09-18
Branch: `defi-liquidation-shock-v0.1`
Posture: `SOURCE_ONLY / OUTCOME_BLIND / FAIL_CLOSED`

## Frozen purpose

Close exact on-chain first-success applicability boundaries for the historically source-supported liquidation decoders without opening any economic outcome.

## Frozen implementation

- plan: `ONCHAIN_FIRST_SUCCESS_BOUNDARY_PLAN_V0.1.md`
- generator: `source/generate_first_success_probe_queue_v0_1.py`
- chunk adjudicator: `source/adjudicate_first_success_probe_chunk_v0_1.py`
- synthetic QA: `source/test_first_success_boundary_tooling_v0_1.py`
- workflow: `.github/workflows/defi-liquidation-first-success-boundary-qa.yml`

QA run: `35349893856` — SUCCESS
Artifact: `10549012208`
Artifact digest: `sha256:84c4d1060b5f4a842730d3446a9e0a757be630cd332f62cb07021a1535dcf9e8`

Generated queue:
- total deterministic chunks: **432**
- Save/Solend: **160**
- Drift v2: **113**
- marginfi v2: **100**
- Kamino Lend: **59**
- max chunk width: **7 days**
- queue SHA256: `d701eb6ef8835429fb3fa5cfb3cfaec370be394cad99d75f6dc1b49a9ef6b3ae`
- queue fingerprint: `5c3a3d78078d9617d305bc2bf34f9493f86ea1781f824997b1fe9037d9980475`
- every generated row at freeze: `NOT_EXECUTED`

The full queue is an upper bound, not a requirement to execute every row. A class stops advancing once its earliest successful candidate is RAW-verified. Protocol execution continues only while at least one applicable class remains unresolved.

## Authority order

1. Corrected Kamino smoke V0.2 remains the immediate next external BigQuery run.
2. If the corrected candidate path is sound, chronological first-success boundary work follows under this freeze.
3. `BIGQUERY_BOUNDED_CANDIDATE_CENSUS_V0_3.sql` is the exact chunk census authority.
4. No chunk may be skipped or reordered based on candidate abundance or any economic information.

## Scientific firewall

`SOURCE_DATA_PASS = false` at this freeze.

No prices, returns, PnL, future direction, threshold tuning, live trading, orders, wallets, exchange mutation, alerts/webhooks or merge to main are authorized.
