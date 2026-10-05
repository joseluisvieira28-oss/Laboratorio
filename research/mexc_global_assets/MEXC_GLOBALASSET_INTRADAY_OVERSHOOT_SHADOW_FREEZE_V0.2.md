# MEXC GLOBAL-ASSET — INTRADAY OVERSHOOT SNAPBACK
## PROSPECTIVE SHADOW EXECUTION FREEZE V0.2

Date: 2026-10-05
Status: FROZEN BEFORE IN-SESSION SHADOW OBSERVATIONS

Scientific authority:
- MEXC-GLOBALASSET-INTRADAY-OVERSHOOT-SNAPBACK-V1.0
- ROBUST_API_FEE_SURVIVOR
- mean gross +20.0820 bps/day
- median gross +18.2504 bps/day
- frozen fee-only net at 16 bps: mean +4.0820 / median +2.2504 bps

Public route authority:
- run 37284578918
- 35/35 depth endpoints accessible
- route parsing PASS
- out-of-session snapshots are explicitly non-evidentiary for execution economics

Prospective observation window:
- only 13:30–20:00 UTC
- frozen V1.0 signal unchanged
- 5m lookback
- external leader dispersion <=10 bps
- abs MEXC move >=40 bps
- abs MEXC excess >=35 bps
- FADE_MEXC_EXCESS
- +5m exit
- 10m global cooldown
- no per-asset tuning

Shadow entry/exit:
- signal may use only closed public candles available at decision time
- capture MEXC public order book immediately after the signal close is observable
- simulate executable taker-side fill from public depth; do not place an order
- capture public order book at the frozen +5m exit
- simulate executable exit fill
- evaluate notional buckets 10 / 25 / 50 / 100 USDT separately
- fee scenario fixed at 16 bps round trip for the primary operational verdict
- also report 12 / 14 / 20 bps for sensitivity
- record public-request latency and data age where exposed

Dependence:
- simultaneous signals remain one equal-weight event basket
- 10m global cooldown unchanged
- daily basket remains the reporting unit

Minimum evidence before operational verdict:
- >=30 admitted shadow event baskets
- >=5 distinct session dates

Execution PASS at a notional bucket requires:
- complete entry and exit executable-book observations
- mean shadow daily net after measured book execution and 16 bps fees >0
- median shadow daily net after measured book execution and 16 bps fees >0
- both chronological shadow halves mean net >0
- no hidden assumption of maker fills

Classification:
- insufficient sample -> `EXECUTION_SHADOW_UNDERPOWERED`
- source/book failures -> `EXECUTION_SOURCE_BLOCKED`
- measured executable economics <=0 -> `EXECUTION_FEASIBILITY_FAIL`
- all frozen gates pass -> `EXECUTION_FEASIBILITY_PASS__MICROLIVE_STILL_NOT_AUTHORIZED`

Strict prohibitions:
- no orders
- no private endpoints
- no account reads
- no wallets
- no exchange mutation
- no live trading
- no post-outcome tuning
