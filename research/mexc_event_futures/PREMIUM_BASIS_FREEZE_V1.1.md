# MEXC EVENT FUTURES LAB — PREMIUM / FAIR-INDEX BASIS FREEZE V1.1

Date: 2026-10-02
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## Prior source result carried forward

V0.6.4.2 passed the current-display equivalence candidate gate:
- 60/60 valid Event Futures page-vs-public-index observations;
- 100% within 1.0 bp;
- median difference 0.0 bp;
- settlement equivalence remains NOT_PROVEN.

The current product matrix source gate also passed:
- BTCUSDT: 10m / 30m / 1H / 1D;
- ETHUSDT: 10m / 30m / 1H / 1D;
- NVDAUSDT: 10m / 30m / 1H / 4H;
- MUUSDT: 10m / 30m / 1H / 4H;
- SPCXUSDT: 10m / 30m / 1H / 4H.

Current payout snapshots observed before this freeze:
- BTCUSDT: 70% Up / 70% Down across its four current horizons;
- ETHUSDT, NVDAUSDT, MUUSDT, SPCXUSDT: 80% Up / 80% Down across their four current horizons.

Those are current observations only, not historical payout assumptions.

## V1.1 hypothesis

Test whether the public MEXC futures fair-price premium relative to index price contains short-horizon directional information relevant to Event Futures.

This is economically distinct from prior:
- raw price momentum/reversal;
- technical chart-state signals;
- cross-asset lead/lag;
- session/calendar bias;
- volatility-shock conditioning;
- OPTIONS-SPOTPERP signal transfer;
- ETF-CME signal transfer.

No V1.1 directional outcomes have been inspected at freeze time.

## Frozen public sources

Index proxy:
`https://contract.mexc.com/api/v1/contract/kline/index_price/{symbol}`

Fair-price proxy:
`https://contract.mexc.com/api/v1/contract/kline/fair_price/{symbol}`

Raw interval:
`Min5`

Each raw Min5 close stamped `s` is treated as observable at `s + 300 seconds`.

Mappings:
- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVIDIA_USDT
- MUUSDT -> MUSTOCK_USDT
- SPCXUSDT -> SPCXSTOCK_USDT

If either series is missing for an asset/period, that asset is SOURCE_BLOCKED for V1.1.

## Frozen feature

At entry time `t`:

`premium_bps[t] = (fair_price[t] - index_price[t]) / index_price[t] * 10000`

Standardize using only the latest 288 completed Min5 premium observations ending at `t`:
- require at least 240 valid observations;
- sample mean and sample standard deviation;
- `z_premium = (premium_bps[t] - trailing_mean) / trailing_sample_sd`;
- zero/non-finite sample SD => no signal.

## Frozen thresholds

Separate pre-frozen cells:
- `|z_premium| >= 1.0`
- `|z_premium| >= 1.5`
- `|z_premium| >= 2.0`

## Frozen modes

- `FOLLOW_PREMIUM`
  - positive z => UP
  - negative z => DOWN

- `FADE_PREMIUM`
  - positive z => DOWN
  - negative z => UP

## Frozen Event Futures horizons

BTCUSDT / ETHUSDT:
- 10m
- 30m
- 60m
- 1440m

NVDAUSDT / MUUSDT / SPCXUSDT:
- 10m
- 30m
- 60m
- 240m

This matches the currently observed product horizon matrix. It is not a claim that the historical Event Futures menu was identical.

## Entry sampling

For event horizon H:
- UTC-aligned anchors;
- entry stride = H;
- non-overlapping target windows within each cell.

Outcome:
`sign(index_price[t+H] - index_price[t])`.

Ties are recorded separately and excluded from binomial N.

## Historical partitions

Discovery:
2026-04-01T00:00:00Z <= t < 2026-08-01T00:00:00Z

Retrospective OOS:
2026-08-01T00:00:00Z <= t < 2026-09-01T00:00:00Z

Historical holdout:
2026-09-01 through 2026-09-30 — LOCKED / MUST NOT BE FETCHED.

## Statistical gate

Primary reference payout:
80%.

Primary break-even directional accuracy:
55.5555556%.

Minimum non-tie N:
- 10m >= 120
- 30m >= 100
- 60m >= 80
- 240m >= 40
- 1440m >= 20

Discovery eligibility requires:
- minimum N;
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- accuracy > 50% in each chronological discovery third;
- computable one-sided exact binomial p-value vs p0=55.5555556%.

Apply Benjamini-Hochberg FDR q=0.05 across the entire eligible V1.1 family.

Only BH-selected cells may open August OOS.

## OOS gate

No parameter changes.

Pass only if:
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- exact one-sided binomial p < 0.05 vs p0=55.5555556%;
- illustrative EV at 80% payout > 0.

Also report:
- EV at 70% payout;
- required payout for zero EV.

No candidate is promoted to exact Event Futures edge from this proxy study.

## Hard boundaries

- No September 2026 access.
- No historical payout fabrication.
- No authenticated exchange call.
- No orders.
- No account mutation.
- No live trading.
- No merge to main.
