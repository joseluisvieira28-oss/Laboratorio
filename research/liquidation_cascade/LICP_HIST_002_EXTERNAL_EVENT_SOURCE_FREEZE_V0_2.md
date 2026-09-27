# LICP-HIST-002 — EXTERNAL EVENT SOURCE FREEZE V0.2

Date: 2026-09-26
Status: SOURCE ONLY / NO BINANCE OUTCOMES

External repository:
- edwinyeeshunwan/forced-or-frantic
- pinned commit: fe8e96ac2d22bc0fd40fd032f3075f2d47ec4f04
- file: data/event_table_liq.parquet

Allowed fields:
- t0
- symbol

All other columns are forbidden to the LICP-HIST-002 trigger/outcome pipeline.

Rationale:
The external event detector is based on rolling long-liquidation notional and its event t0 is independent of Binance Futures outcomes. The published deleverage/churn classification is excluded because it uses future OI inside t0→t0+2h.

Causality correction:
observable_trigger_time = t0 + 5 minutes.

Historical partition frozen before Binance price outcomes:
- DISCOVERY: 2025-08-10 through 2025-10-31 UTC
- HOLDOUT: 2025-11-01 through 2025-12-31 UTC

The HOLDOUT must not be queried by Discovery code.

Source probe may report only:
- row count
- symbol counts
- t0 minimum/maximum
- month counts

It must not expose or calculate any external outcome/classification field.
