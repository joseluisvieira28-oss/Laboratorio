# LICP-HIST-XALT-003 — HOLDOUT CANDIDATE SERIALIZATION V0.1

Date: 2026-09-26
Status: FROZEN BEFORE HOLDOUT OPEN

## Discovery lineage
Pre-outcome Discovery freeze: LICP_HIST_XALT_003_PRE_OUTCOME_FREEZE_V0_1.md.

Discovery decision: DISCOVERY_SURVIVOR_EXISTS.

The deterministic selection rule frozen before Discovery selected:
- target: SOL
- horizon: 60 minutes
- primary observable entry proxy: t0 + 6 minutes
- direction: SHORT / SELL continuation after BTC long-liquidation ignition
- MEXC transfer hurdle: 16 bps

Frozen Discovery statistics for the selected candidate:
- n = 45
- mean gross = 25.821043849952094 bps
- median gross = 20.067922198210084 bps
- mean transfer-ceiling net = 9.821043849952094 bps
- positive Discovery months = 2

## Locked single-pass holdout
Window:
- 2025-11-01T00:00:00Z through 2025-12-31T23:59:59.999999Z

Event source:
- pinned Hyperliquid event table commit fe8e96ac2d22bc0fd40fd032f3075f2d47ec4f04
- fields t0 and symbol only
- BTC events only

Price source:
- Binance Vision USD-M Futures SOLUSDT 1m klines
- November and December 2025 only

Outcome:
gross_directional_bps = (entry_open - future_open) / entry_open * 10,000

Entry:
- primary = t0 + 6 minutes

Future:
- entry + 60 minutes

## Holdout PASS gate
PASS only if ALL are true:
- n >= 20;
- pooled mean gross > 16 bps;
- pooled median gross > 0;
- BOTH holdout months with observations have positive mean gross.

Otherwise:
LICP_HIST_XALT_003_HOLDOUT_FAIL.

No alternative target.
No alternative horizon.
No delay change.
No reversal rescue.
No threshold tuning.
No second holdout attempt.
No 2026 data.
No live-trading authority.
