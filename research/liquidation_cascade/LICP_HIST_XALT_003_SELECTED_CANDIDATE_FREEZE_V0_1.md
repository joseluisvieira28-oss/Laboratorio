# LICP-HIST-XALT-003 — SELECTED CANDIDATE / HOLDOUT FREEZE V0.1

Date: 2026-09-26
Status: FROZEN BEFORE HOLDOUT OPEN

## Discovery provenance
Pre-outcome protocol: LICP_HIST_XALT_003_PRE_OUTCOME_FREEZE_V0_1.md
Discovery decision: DISCOVERY_SURVIVOR_EXISTS
BTC ignition events: 45

## Deterministically selected candidate
- target: SOLUSDT
- direction: SHORT / SELL continuation after BTC long-liquidation ignition
- observable trigger: t0 + 5 minutes
- PRIMARY entry proxy: t0 + 6 minutes
- horizon: 60 minutes after entry
- MEXC transfer hurdle: 16 bps
- Discovery mean gross: 25.821043849952094 bps
- Discovery median gross: 20.067922198210084 bps
- Discovery mean transfer-ceiling net: 9.821043849952094 bps
- positive Discovery months: 2 of 3
- n: 45

ETH/60m also survived Discovery but is NOT eligible for the primary holdout because the frozen selection rule chose the candidate with the highest PRIMARY mean transfer-ceiling net.

## Locked holdout
2025-11-01T00:00:00Z through 2025-12-31T23:59:59.999999Z.

The holdout runner MUST:
- use only BTC t0 rows from the same pinned external event table;
- download only SOLUSDT official Binance Vision USD-M Futures 1m klines for 2025-11 and 2025-12;
- evaluate only PRIMARY entry t0+6m and horizon 60m;
- never compare ETH or alternative horizons;
- never alter the 16 bps transfer hurdle after outcomes;
- open the holdout exactly once.

## Holdout survival rule
The frozen SOL/60m candidate survives only if:
- n >= 20 holdout BTC ignition events;
- pooled mean gross > 16 bps;
- pooled median gross > 0;
- both holdout months have positive mean gross.

If any criterion fails: LICP_HIST_XALT_003_HOLDOUT_NO_EDGE.

If all pass: LICP_HIST_XALT_003_HOLDOUT_SURVIVOR.

This is still coarse price-continuation evidence, NOT executable PnL and NOT live-trading authority.
No rescue. No threshold/horizon/asset switching. No 2026 data.
