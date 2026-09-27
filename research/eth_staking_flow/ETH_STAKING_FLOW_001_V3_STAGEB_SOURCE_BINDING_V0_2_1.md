# ETH-STAKING-FLOW-001 — V3 STAGE-B SOURCE BINDING V0.2.1

Date frozen: 2026-09-27
Status: FROZEN BEFORE ANY V0.2.1 STAGE-B MARKET ACCESS

Parent scientific authority remains unchanged:
- ETH_STAKING_FLOW_001_V3_INDEPENDENT_REPLICATION_AUTHORITY_V0_1.md
- ETH_STAKING_FLOW_001_V3_STAGEB_MARKET_IMPLEMENTATION_ADDENDUM_V0_1.md

## Purpose

Bind the unchanged Stage-B market/outcome implementation to the prospective Stage-A V0.2.1 receipt and ledger produced by the exact-epoch fct_validator_balance remediation.

Required source inputs:
- ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_V0_2_1.json
- ETH_STAKING_FLOW_001_V3_REPLICATION_SOURCE_LEDGER_V0_2_1.json

## Trigger gate

Stage B may execute only if the receipt proves:
- classification == SOURCE_REPLICATION_PASS
- observed_date_count == 608
- control_exact_match_count == 3
- recovered_missing_date_count == 7
- legacy_preserved_date_count == 601
- no market/source firewall violation
- receipt/ledger daily_series_sha256 exact match.

Any other state stops before market access.

## Scientific rules unchanged

No change to:
- predictor;
- q80 / prior-90 rule;
- current-day exclusion;
- direction LONG ETH;
- ETHUSDT spot;
- t+1 entry;
- t+8 exit;
- non-overlap;
- 10 bps BASE;
- 20 bps STRESS;
- R1/R2 windows;
- bootstrap;
- block-level gates;
- leave-one-block-out gates;
- concentration gate.

No market date after 2026-09-08.
No source date after 2026-08-31.
No tuning.
No live trading/orders/wallet/exchange mutation.
No main merge.
