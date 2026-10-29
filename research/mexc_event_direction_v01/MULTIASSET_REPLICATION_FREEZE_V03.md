# Event Futures Multiasset V0.3 — Frozen All-Cell Date Replication
Frozen 2026-10-29 BEFORE accessing the price outcomes for 2026-10-26 or 2026-10-27 in this experiment.

## Parent, no changes to scientific strategies
Use exact functions and families from research/mexc_event_direction_v01/multiasset_historical_v02.py on parent head 124cb49f997f57551757d30fc96cb5114fa091ea: BTC_USDT, ETH_USDT, NVIDIA_USDT, SPCXSTOCK_USDT, MUSTOCK_USDT; UP_ALWAYS, DOWN_ALWAYS, ROC3_CONT, ROC3_REV; 10m and 30m; ALL_24H and US_REGULAR_PROXY; payout q scenarios 0.40/0.70/0.80/0.85. All 80 cells must be included. NO selection of 15 positive first-window cells, no threshold, no new sides, no exclusion of low-performers.

## New date window
Exactly 2026-10-26 00:00 UTC inclusive until 2026-10-28 00:00 UTC exclusive. This is 576 Min5 index-open candles per asset, strict 100% full grid and source SHA256 recorded. Historical availability will be validated after request and failure means source BLOCK, not imputation.

## US regular reference hours
The prior first-window logic 2026-10-22/23 used 13:30..20:00 UTC, corresponding to 09:30..16:00 America/New_York when US was in daylight time. US DST switched on 2026-10-25. The SAME stock-market reference session for 2026-10-26/27 therefore corresponds to 14:30..21:00 UTC, evaluated through America/New_York timezone. This is a time conversion correction BEFORE seeing these new outcomes, not a change in the market model. The US_REGULAR_PROXY is not evidence that the MEXC Event Futures product had this trading schedule.

## Protocol
Non-overlapping fixed UTC-midnight anchored decision clocks (every H), strictly preceding feature open at t-15m and t-5m, hypothetical price INDEX_OPEN(t) vs INDEX_OPEN(t+H), positive/negative/equal => WIN/LOSS/TIE. Equal features abstain, missing bars block entire study. Date-by-date returns for all cells. q payout is hypothetical, NOT actual historical MEXC Event Futures payout. Index bar OPEN is not proven Event Futures server-assigned openPrice or settle price.

## Scientific language
The original 22/23 Oct window is already-open Discovery. This 26/27 Oct window was not used to select this rule family within THIS event-futures experiment, but it is still a short historical replay, not a protected independently sealed holdout or live forward study. No survivor, no capital, no real trading, no September holdout, no pricing/PnL certainty. Event products observed ONLINE only on Oct29; historical eligibility is unknown. MLIUSDT remains UNKNOWN_IDENTITY and not part of this test. Retain parent negative studies and previous #107 NO_EDGE.
