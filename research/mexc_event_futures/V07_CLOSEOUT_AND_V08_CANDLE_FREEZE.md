# MEXC EVENT FUTURES LAB — V0.7 CLOSEOUT + V0.8 CANDLE MORPHOLOGY FREEZE

Date: 2026-10-02
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## V0.7 closeout

Frozen calendar/session cells tested:
1,960.

Basic discovery-eligible:
19.

Benjamini-Hochberg FDR q=0.05 selected:
0.

August OOS opened:
0.

Verdict:
**NO_PROXY_SURVIVOR_AT_FROZEN_V07_GATE**

September 2026 holdout remained LOCKED / NOT FETCHED.

## Why V0.8 is scientifically distinct

V0.8 tests OHLC candle morphology and price-location information that was not used by:
- simple trailing-return V0.3.1;
- technical-state V0.4;
- cross-asset V0.5;
- calendar/session V0.7.

No V0.8 outcomes have been inspected at freeze time.

## Source and clock

Public MEXC standard-futures index-price K-lines:
`https://contract.mexc.com/api/v1/contract/kline/index_price/{symbol}`

Raw source interval:
`Min5`

Each raw Min5 bar stamped `s` is treated as completed/observable at `s + 300 seconds`.

Mappings:
- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVIDIA_USDT
- MUUSDT -> MUSTOCK_USDT
- SPCXUSDT -> SPCXSTOCK_USDT

This remains a standard-futures index-price proxy, not exact Event Futures settlement history.

## Frozen chart timeframes

- 5m
- 15m
- 60m
- 240m

Higher-timeframe OHLC bars are deterministically resampled from completed Min5 bars:
- open = first Min5 open;
- high = maximum Min5 high;
- low = minimum Min5 low;
- close = last Min5 close;
- higher-timeframe timestamp = end of the completed higher-timeframe bucket.

Only completed bars ending at or before entry time are usable.

## Frozen Event horizons

- 10m
- 30m
- 60m
- 1440m

## Frozen candle hypotheses

1. `BODY_CONT`
   - close > open => UP
   - close < open => DOWN

2. `BODY_REV`
   - opposite of BODY_CONT

3. `CLOSE_LOCATION_CONT`
   - close location within candle range >= 0.80 => UP
   - <= 0.20 => DOWN
   - otherwise no signal

4. `CLOSE_LOCATION_REV`
   - opposite of CLOSE_LOCATION_CONT

5. `WICK_REJECTION`
   - lower wick >= 2 × upper wick and lower wick > body => UP
   - upper wick >= 2 × lower wick and upper wick > body => DOWN
   - otherwise no signal

6. `WICK_FOLLOW`
   - opposite of WICK_REJECTION

7. `ENGULFING_CONT`
   - current real body fully engulfs previous real body;
   - bullish engulfing => UP;
   - bearish engulfing => DOWN;
   - otherwise no signal

8. `LARGE_BODY_CONT`
   - current body/range >= 0.70;
   - current range >= 1.5 × median range of prior 20 completed chart bars;
   - predict current body direction;
   - otherwise no signal

9. `LARGE_BODY_REV`
   - same trigger as LARGE_BODY_CONT, opposite direction.

10. `HIGHLOW_BREAKOUT_CONT`
    - close > max(high of prior 20 bars) => UP
    - close < min(low of prior 20 bars) => DOWN
    - otherwise no signal

No parameter alternatives are permitted inside V0.8.

## Entry spacing

For a chart timeframe T and Event horizon H:
`entry_stride = max(T, H)`

Candidate entries must:
- coincide with a completed chart-bar end;
- have exact proxy close at entry and at t+H;
- be separated by at least entry_stride within each cell.

## Partitions

Discovery:
2026-04-01T00:00:00Z <= t < 2026-08-01T00:00:00Z

Retrospective OOS:
2026-08-01T00:00:00Z <= t < 2026-09-01T00:00:00Z

Historical holdout:
2026-09-01 through 2026-09-30 — LOCKED / MUST NOT BE FETCHED.

## Statistical gates

Reference payout:
80%.

Break-even accuracy:
55.5555556%.

Discovery minimum non-tie N:
- 10m >= 120
- 30m >= 100
- 60m >= 80
- 1d >= 30

Basic eligibility requires:
- minimum N;
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- accuracy > 50% in each chronological discovery third.

For all basic-eligible cells:
- one-sided exact binomial p-value vs p0=55.5555556%.

Apply Benjamini-Hochberg FDR q=0.05 across the full V0.8 eligible family.

Only BH-selected cells may open August OOS.

## OOS gate

No changes to asset, timeframe, candle rule or horizon.

Pass requires:
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- one-sided exact binomial p-value vs 55.5555556% < 0.05;
- EV at illustrative 80% payout > 0.

Also report EV at 70/75/80/85/90% payout and required payout for EV=0.

Any survivor remains a PROXY CANDIDATE only.

## Hard boundaries

- No September 2026 data.
- No authenticated MEXC request.
- No order submission.
- No account mutation.
- No exact Event Futures promotion.
- No post-outcome tuning.
- No merge to main.
