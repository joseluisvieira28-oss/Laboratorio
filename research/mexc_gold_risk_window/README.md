# MEXC-GOLD-RISK-WINDOW-001A — Pre-registered Historical Event Test

Status: research-only, fail-closed. No trading, no private endpoints, no account reads, no main mutation.

## Frozen event windows
- CPI 2026-09-11: cut 12:20 UTC; macro T0 12:30; restore 12:35; study 11:30–13:30.
- FOMC 2026-09-16: cut 17:50 UTC; macro T0 18:00; restore 18:05; study 17:00–19:00.

## Symbols
- XAU_USDT
- XAUT_USDT
- XAG_USDT

## Primary metrics
1. Last close vs Index close, bps.
2. Fair close vs Index close, bps.
3. XAU vs XAUT Last-price basis deviation from PRE median, bps.
4. Restoration compression: median absolute dislocation during the 5 minutes before restoration vs the 10 minutes after restoration.
5. Funding settlements near each event.

## Frozen execution-cost screens
- API taker: 8 bps per side.
- Single-instrument taker round trip: 16 bps.
- Two-leg XAU/XAUT taker round trip: 32 bps.

These are magnitude screens only. 1-minute OHLC cannot prove bid/ask fills.

## Decision
- BLOCKED_DATA_COVERAGE: public historical series are incomplete or unavailable.
- NO_EDGE_1M_MAGNITUDE_SCREEN: even the maximum close-based dislocation is below the applicable conservative fee floor.
- HISTORICAL_MAGNITUDE_CANDIDATE_NEEDS_EXECUTION_DATA: dislocation magnitude exceeds fee floor; forward L1/L2/trade collector is mandatory before any SURVIVES verdict.

No threshold optimization after observing outcomes.
