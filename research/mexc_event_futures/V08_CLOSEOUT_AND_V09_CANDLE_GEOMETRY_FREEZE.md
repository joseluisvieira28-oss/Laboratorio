# MEXC EVENT FUTURES LAB — V0.8 CLOSEOUT + V0.9 CANDLE-GEOMETRY FREEZE

Date: 2026-10-02
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## V0.8 closeout

V0.8 tested standardized pre-entry volatility shocks across all five displayed Event Futures underlyings.

Result:
- frozen discovery cells: 480
- basic discovery-eligible cells: 25
- Benjamini-Hochberg FDR q=0.05 selected: 0
- August OOS opened: 0
- September 2026 holdout: LOCKED / NOT FETCHED

Verdict:
**NO_PROXY_SURVIVOR for the frozen volatility-shock continuation/reversal family.**

## V0.9 hypothesis family

Test whether completed candle geometry — body strength, wick rejection, and engulfing structure — predicts the sign of the next Event Futures horizon strongly enough to clear the fixed 80%-payout reference hurdle.

This is distinct from V0.3.1/V0.4/V0.5/V0.7/V0.8 because it uses OHLC geometry rather than close-only trend, indicator, calendar, cross-asset, or volatility-shock state.

No V0.9 outcomes have been inspected at freeze time.

## Source and clock

Public MEXC standard-futures index-price K-lines:
`https://contract.mexc.com/api/v1/contract/kline/index_price/{symbol}`

Raw interval:
`Min5`

Each raw Min5 candle timestamp `s` is treated as candle START.
The full OHLC candle becomes observable only at `s + 300 seconds`.

Assets:
- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVIDIA_USDT
- MUUSDT -> MUSTOCK_USDT
- SPCXUSDT -> SPCXSTOCK_USDT

September 2026 remains LOCKED and MUST NOT be fetched.

## Frozen chart timeframes

- 5m
- 15m
- 60m
- 240m

Higher timeframes are built only from completed contiguous Min5 candles.
A higher-timeframe candle ending at time `t` is observable at `t`.

## Frozen Event Futures horizons

- 10m
- 30m
- 60m
- 1440m

## Frozen candle strategies

All ratios use:
- range = high - low;
- body = abs(close - open);
- upper_wick = high - max(open, close);
- lower_wick = min(open, close) - low.

If range <= 0, no signal.

1. `STRONG_BODY_CONT`
   - body/range >= 0.70;
   - bullish candle => UP;
   - bearish candle => DOWN.

2. `STRONG_BODY_REV`
   - same qualification;
   - bullish candle => DOWN;
   - bearish candle => UP.

3. `UPPER_WICK_REJECT`
   - upper_wick/range >= 0.55;
   - body/range <= 0.35;
   - predict DOWN.

4. `LOWER_WICK_REJECT`
   - lower_wick/range >= 0.55;
   - body/range <= 0.35;
   - predict UP.

5. `ENGULFING_CONT`
   - current body engulfs prior candle body:
     current body low <= prior body low AND current body high >= prior body high;
   - current candle must have body/range >= 0.50;
   - bullish current candle => UP;
   - bearish current candle => DOWN.

6. `ENGULFING_REV`
   - same qualification;
   - predict opposite current candle direction.

No alternative body/wick thresholds are permitted inside V0.9.

## Entry sampling

For chart timeframe C and event horizon H:
`entry_stride = max(C, H)`.

Entry timestamp must align to both a completed chart-candle end and the frozen stride.
This reduces repeated reuse of the same candle and overlapping outcomes.

Outcome:
sign(index_close[t + H] - index_close[t]).

Ties are recorded separately and excluded from binomial N.

## Partitions

Discovery:
2026-04-01T00:00:00Z <= t < 2026-08-01T00:00:00Z

Retrospective OOS:
2026-08-01T00:00:00Z <= t < 2026-09-01T00:00:00Z

Historical holdout:
2026-09-01 through 2026-09-30 — LOCKED / NOT FETCHED.

## Discovery gate

Illustrative payout reference:
80%.

Break-even directional accuracy:
55.5555556%.

Minimum non-tie N:
- 10m >= 80
- 30m >= 60
- 60m >= 50
- 1d >= 15

A cell is discovery-eligible only if:
- minimum N is met;
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- accuracy > 50% in each of three chronological discovery thirds;
- one-sided exact binomial p-value vs p0=55.5555556% is computable.

Apply Benjamini-Hochberg FDR q=0.05 across the entire eligible V0.9 family.

Only BH-selected cells may open August OOS.

## OOS gate

No parameter change.

Pass only if:
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- one-sided exact binomial p < 0.05 vs p0=55.5555556%;
- illustrative EV at 80% payout > 0.

Any survivor remains a **PROXY CANDIDATE**, not an exact Event Futures edge.

## Hard boundaries

- No September 2026 data.
- No historical payout fabrication.
- No exact Event Futures profitability claim.
- No authentication.
- No orders.
- No account mutation.
- No merge to main.
