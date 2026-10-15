# ABSORPTION-FAILED-AUCTION-001 — PARENT PASS_STRONG AUTHORITY RECEIPT

Date: 2026-10-01
Parent: TV-FOOTPRINT-CALIBRATION-001
Parent terminal classification: **PASS_STRONG**
Parent terminal closeout commit: `39bd1f9c5721934beb648ecfa2f777fe4ff7234d`
Parent workflow run: `36865095179`
Parent artifact: `11163421403`

## Parent terminal evidence

- terminal bars: 2,016
- matched coverage: 100%
- Binance source completeness: 100%
- median absolute relative volume error: 3.025204563714369e-14
- delta sign agreement: 85.267857%
- Spearman: 0.8403088547066349
- Pearson: 0.9279539402657925
- terminal TV sample SHA256: `83ee7153c8e285caf9bba27d92da1aaf84304fde494c90f0735129b8ab8b687e`

## Causal child opening

Parent PASS_STRONG closeout commit timestamp:
2026-10-01 13:02:38 UTC.

First 5-minute bar whose open is strictly after that authority timestamp:

- event-open bar open: 2026-10-01 13:05:00 UTC
- event-open boundary / close: 2026-10-01 13:10:00 UTC
- event_open_boundary_ms: 1790860200000

Bars before this boundary may serve only as frozen causal rolling history where the protocol permits. They cannot become child events.

## Authority state

- event_collection_open: TRUE
- economic_outcomes_unlocked: FALSE
- R5/R15/R30/R60/R240 inspection: FORBIDDEN while sealed
- trading_authority: NONE

PASS_STRONG opens prospective event classification only. It does not open economic outcomes and does not create an edge or a trading strategy.
