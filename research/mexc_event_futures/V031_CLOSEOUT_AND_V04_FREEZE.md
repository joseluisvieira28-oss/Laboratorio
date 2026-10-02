# MEXC EVENT FUTURES LAB — V0.3.1 CLOSEOUT + V0.4 PRE-OUTCOME FREEZE

Date: 2026-10-02

## V0.3.1 closeout

Clock-corrected simple proxy test completed successfully.

Source:
MEXC standard-futures index-price Min5 proxy, with each K-line close mapped to bucket-end time.

Assets with usable source:
BTCUSDT, ETHUSDT, NVDAUSDT, MUUSDT, SPCXUSDT.

Frozen simple family:
- CONTINUATION
- REVERSAL
- chart lookbacks 5m / 15m / 1h / 4h / 1d
- event horizons 10m / 30m / 1h / 1d

Result:
- discovery passers: 0
- August OOS cells evaluated: 0
- OOS survivors: 0
- September 2026 holdout: LOCKED / NOT FETCHED

Verdict:
**NO_PROXY_SURVIVOR for the frozen simple continuation/reversal family.**

This is not a verdict on all Event Futures strategies and is not an exact Event Futures economic backtest.

## Why V0.4 is scientifically distinct

V0.4 tests pre-specified chart-state hypotheses rather than raw trailing-return continuation/reversal.

No V0.4 outcomes have been inspected at freeze time.
August OOS remains unopened for V0.4 because V0.3.1 had no discovery passer.

## V0.4 source and clock

Primary source:
`https://contract.mexc.com/api/v1/contract/kline/index_price/{symbol}`

Raw interval:
`Min5`

Every raw Min5 close stamped `s` is mapped to observable proxy time `s + 300 seconds`.

No September 2026 timestamp may be fetched or evaluated.

## Assets

- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVIDIA_USDT
- MUUSDT -> MUSTOCK_USDT
- SPCXUSDT -> SPCXSTOCK_USDT

## Event horizons

- 10m
- 30m
- 60m
- 1440m

## Chart timeframes

- 5m
- 15m
- 60m
- 240m
- 1440m

At an entry timestamp, only a fully completed chart close at or before entry may be used.

To reduce repeated-signal / overlapping-outcome inflation, entry stride is frozen to:
`max(event_horizon, chart_timeframe)`.

## Frozen strategy families

All parameters below are frozen before V0.4 outcomes.

1. `EMA_TREND_9_21`
   - EMA9 > EMA21 => UP
   - EMA9 < EMA21 => DOWN
   - equality => no signal

2. `RSI14_EXTREME_REV`
   - RSI14 < 30 => UP
   - RSI14 > 70 => DOWN
   - otherwise no signal

3. `DONCHIAN20_BREAKOUT`
   - current close > max(previous 20 chart closes) => UP
   - current close < min(previous 20 chart closes) => DOWN
   - otherwise no signal

4. `BOLL20_2_REV`
   - current close < prior-20 mean - 2 population SD => UP
   - current close > prior-20 mean + 2 population SD => DOWN
   - otherwise no signal

5. `STREAK3_REV`
   - 3 consecutive positive chart returns => DOWN
   - 3 consecutive negative chart returns => UP
   - otherwise no signal

6. `STREAK3_CONT`
   - 3 consecutive positive chart returns => UP
   - 3 consecutive negative chart returns => DOWN
   - otherwise no signal

7. `ROC3_CONT`
   - current close > close 3 chart bars ago => UP
   - current close < close 3 chart bars ago => DOWN
   - equality => no signal

8. `RANGE20_POSITION_REV`
   - using min/max of prior 20 chart closes:
   - current close in/above top 20% of prior range => DOWN
   - current close in/below bottom 20% => UP
   - otherwise no signal

No parameter alternatives are permitted inside V0.4.

## Partitions

Discovery:
2026-04-01T00:00:00Z <= t < 2026-08-01T00:00:00Z

Retrospective OOS:
2026-08-01T00:00:00Z <= t < 2026-09-01T00:00:00Z

Historical holdout:
2026-09-01 through 2026-09-30 — LOCKED.

## Discovery gate

Reference break-even for an illustrative 80% payout:
55.5555556%.

A cell is eligible only if:
- non-tie N >= 120 for 10m;
- N >= 100 for 30m;
- N >= 80 for 60m;
- N >= 40 for 1d;
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- accuracy > 50% in each chronological discovery third.

For every eligible cell, calculate a one-sided exact binomial p-value against p0 = 55.5555556%.

Apply Benjamini-Hochberg FDR q=0.05 across the entire eligible discovery family.

Only BH-selected cells may open August OOS.

## OOS gate

No parameter changes.

An OOS cell passes only if:
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- one-sided exact binomial p-value vs 55.5555556% < 0.05;
- unit EV under illustrative 80% payout > 0.

Any survivor remains a **PROXY CANDIDATE**, not an Event Futures edge.

## Product-level blockers remain

Exact Event Futures profitability remains unproven until:
- historical payout-at-entry is available or prospectively recorded;
- Event Futures settlement-index equivalence is proven;
- exact entry/expiry price timestamp semantics are proven.

No live trading. No account mutation. No merge to main.
