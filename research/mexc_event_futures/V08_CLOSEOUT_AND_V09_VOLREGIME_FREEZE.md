# MEXC EVENT FUTURES LAB — V0.8 CLOSEOUT + V0.9 VOLATILITY-REGIME FREEZE

Date: 2026-10-02
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## V0.8 closeout

Frozen OHLC candle-morphology cells tested:
640.

Basic discovery-eligible:
16.

Benjamini-Hochberg FDR q=0.05 selected:
0.

August OOS opened:
0.

Source:
- BTCUSDT: available
- ETHUSDT: available
- NVDAUSDT: available
- MUUSDT: available
- SPCXUSDT: OHLC source blocked in V0.8

Verdict:
**NO_PROXY_SURVIVOR_AT_FROZEN_V08_GATE**

September 2026 holdout remained LOCKED / NOT FETCHED.

## Why V0.9 is scientifically distinct

V0.9 tests whether directional continuation/reversal behaves differently under objectively defined volatility regimes.

The regime rule is frozen before any V0.9 outcome inspection and is not tuned from Event Futures outcomes.

## Source and clock

Public MEXC standard-futures index-price Min5 proxy:
`https://contract.mexc.com/api/v1/contract/kline/index_price/{symbol}`

Each raw Min5 close stamped `s` is treated as observable at `s + 300 seconds`.

Mappings:
- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVIDIA_USDT
- MUUSDT -> MUSTOCK_USDT
- SPCXUSDT -> SPCXSTOCK_USDT

Close-only source is sufficient for V0.9.

## Frozen directional lookbacks

- 15m
- 60m
- 240m

Signal:
`sign(price[t] - price[t-lookback])`

Modes:
- CONTINUATION = same sign
- REVERSAL = opposite sign

Zero trailing move = no signal.

## Frozen volatility windows

Realized volatility is the population standard deviation of 5-minute log returns over the immediately preceding:

- 60m
- 240m
- 1440m

The current return ending at entry time may be included because its close is observable at entry.

## Frozen regime baseline

For a volatility window W, compute the median realized volatility value observed at 5-minute timestamps over the trailing 7 calendar days, excluding the current timestamp but using only data observable by entry time.

Regimes:

- HIGH_VOL: current RV >= 1.50 × trailing-7d median RV
- LOW_VOL: current RV <= 0.67 × trailing-7d median RV
- MID_VOL: otherwise

V0.9 tests only HIGH_VOL and LOW_VOL.

If baseline median is zero/unavailable, no signal.

No alternate multipliers or baseline windows are permitted in V0.9.

## Frozen Event horizons

- 10m
- 30m
- 60m
- 1440m

## Frozen test grid

For every source-available asset:

- 3 directional lookbacks
- 3 volatility windows
- 2 regimes
- 2 directional modes
- 4 Event horizons

Maximum:
5 × 3 × 3 × 2 × 2 × 4 = 720 cells.

## Entry spacing

Within each cell:
`entry_stride = max(event_horizon, directional_lookback, volatility_window)`

Only exact 5-minute proxy timestamps are eligible.

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
- 10m >= 80
- 30m >= 70
- 60m >= 60
- 1d >= 25

Basic eligibility:
- minimum N;
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- accuracy > 50% in each chronological discovery third.

Every basic-eligible cell receives:
- one-sided exact binomial p-value vs p0 = 55.5555556%.

Apply Benjamini-Hochberg FDR q=0.05 across the full V0.9 eligible family.

Only BH-selected cells may open August OOS.

## OOS gate

No parameter changes.

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
- No post-outcome regime tuning.
- No merge to main.
