# ETH-STAKING-FLOW-001 — V3 STAGE-B SOURCE BINDING V0.2.0

Date frozen: 2026-09-27
Status: FROZEN BEFORE ANY V0.2.0 STAGE-B MARKET ACCESS

## Parent scientific authority

Unchanged:
- ETH_STAKING_FLOW_001_V3_INDEPENDENT_REPLICATION_AUTHORITY_V0_1.md
- ETH_STAKING_FLOW_001_V3_STAGEB_MARKET_IMPLEMENTATION_ADDENDUM_V0_1.md

## Purpose

Bind the already-frozen Stage-B implementation to the prospectively frozen Stage-A V0.2.0 source receipt/ledger.

Only implementation binding changes:

Old hardcoded inputs:
- ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_1_6.json
- ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_LEDGER_V0_1_6.json

New hardcoded inputs:
- ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_2_0.json
- ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_LEDGER_V0_2_0.json

## Trigger

Stage B remains physically closed until both new files are durably present on the same research branch and the receipt proves:
- classification == SOURCE_REPLICATION_PASS
- observed_date_count == 608
- source-only firewalls clean
- ledger SHA binding exact.

Any other state stops before market access.

## Scientific invariants

No change to:
- predictor;
- q80 threshold;
- prior-90 lookback;
- current-day exclusion;
- LONG ETHUSDT spot;
- t+1 entry;
- t+8 exit / 7-day hold;
- non-overlap;
- 10 bps BASE;
- 20 bps STRESS;
- R1 / R2 windows;
- source/market ceilings;
- bootstrap;
- V3 promotion gates;
- leave-one-block-out rules;
- concentration gate.

No market date after 2026-09-08.
No source date after 2026-08-31.
No post-outcome tuning.
No live trading/orders/wallets/exchange mutation.
No main merge.
