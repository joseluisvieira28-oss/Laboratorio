# BITGET MAKER MICROSTRUCTURE — V0.2.1 + DEPTH CADENCE V0.3 CLOSEOUT

Date: 2026-10-05

## Parent execution study

Technical identity-fixed run:
- branch: `bitget-maker-microstructure-v0.2.1-identityfix-2026-10-05`
- run: `37272037117`
- family artifact ID: `11329085449`
- family artifact SHA256: `0a1be1d380515ebaaf0068860a2cd2f64350de1cb4ce9a99f6c7b900283fd5ca`

The V0.2.1 technical amendment restored the exact frozen parent signal identities:
- HOODUSDT: 1148
- COINUSDT: 986
- ARMUSDT: 923
- AAPLUSDT: 86

No signal threshold, direction, horizon, fee, latency, queue, TTL, fill rule or execution gate changed.

Family verdict:
`NO_MAKER_EXECUTION_SURVIVOR_AT_FROZEN_V02_GATE`

All four assets were classified:
`MICROSTRUCTURE_DATA_BLOCKED`

Observed placement quote coverage:
- HOOD: 8.36%
- COIN: 9.23%
- ARM: 9.53%
- AAPL: 9.30%

Frozen gate:
- >=90% parent-signal quote observability with quote age <=5 seconds.

## Source-cadence diagnostic

Source-only branch:
`bitget-depth-cadence-v0.3-source-audit-2026-10-05`

Run:
`37272373282`

Artifact ID:
`11328776062`

Artifact SHA256:
`9b1d0325921a7fe2d77d6282013124ebfb81c739583401ad54b015aa5896a9fe`

Burned source date:
`2026-09-16`

For all four assets and for both deptType 1 and deptType 2:
- unique historical snapshots/day: 3509
- median snapshot gap: 26 seconds
- neutral every-second coverage with latest quote age <=5s: 6.7716535%

Verdict:
`LEVEL1_HISTORICAL_CADENCE_STRUCTURALLY_INCOMPATIBLE_WITH_FROZEN_90PCT_OBSERVABILITY_GATE`

Level500 timestamp cadence was identical and does not repair the blocker.

## Final classification

`BITGET_MAKER_EDGE_SCIENTIFICALLY_INTERESTING__HISTORICAL_MICROSTRUCTURE_VALIDATION_SOURCE_BLOCKED`

Do not lower the 5-second staleness gate or 90% observability gate to rescue this outcome window.

A future legitimate route would require:
- genuinely high-frequency historical Bitget L1/L2 data frozen before use; or
- a prospective read-only shadow collector of live public book/trades under a new forward freeze.

No private endpoints, account reads, orders, wallets, exchange mutation or live trading were used.
