# MEXC EVENT FUTURES LAB — CROSS-ASSET LEAD/LAG FREEZE V0.5

Date: 2026-10-02
Status: PRE-OUTCOME / RESEARCH-ONLY / FAIL-CLOSED

## Prior result preserved

V0.4 tested 800 frozen technical chart-state cells across BTCUSDT, ETHUSDT, NVDAUSDT, MUUSDT and SPCXUSDT.
27 cells met the basic discovery eligibility screen, but **0 survived the pre-frozen Benjamini-Hochberg FDR q=0.05 selection**.
Therefore August OOS remained unopened for V0.4.

V0.5 is an economically distinct hypothesis family: cross-asset information propagation.

## Hypothesis

A recent move in one displayed Event Futures underlying may lead or inversely lead the subsequent direction of another displayed underlying over a fixed Event Futures horizon.

No V0.5 directional outcomes have been inspected at freeze time.

## Source and clock

Public MEXC standard-futures index-price Min5 proxy:
`https://contract.mexc.com/api/v1/contract/kline/index_price/{symbol}`

Each Min5 close with raw bucket timestamp `s` is treated as observable at `s + 300 seconds`.

Mappings:
- BTCUSDT -> BTC_USDT
- ETHUSDT -> ETH_USDT
- NVDAUSDT -> NVIDIA_USDT
- MUUSDT -> MUSTOCK_USDT
- SPCXUSDT -> SPCXSTOCK_USDT

This remains a proxy, not proven Event Futures settlement history.

## Frozen directed pairs

Every ordered leader -> target pair among the five assets, excluding self-pairs.

Count:
5 targets × 4 possible leaders = 20 directed pairs.

## Frozen leader lookbacks

- 5m
- 15m
- 60m
- 240m

## Frozen Event Futures horizons

- 10m
- 30m
- 60m
- 1440m

## Frozen signal modes

- FOLLOW_LEADER: sign(leader price[t] - leader price[t-lookback])
- FADE_LEADER: opposite of that sign

Zero leader return = no signal.

Target outcome:
sign(target price[t+horizon] - target price[t])

Target tie = tie.

## Entry stride

To reduce overlapping outcomes and repeated leader-information reuse:

`entry_stride = max(horizon, leader_lookback)`

Entries are aligned to that stride in UTC.

## Partitions

Discovery:
2026-04-01T00:00:00Z <= t < 2026-08-01T00:00:00Z

Retrospective OOS:
2026-08-01T00:00:00Z <= t < 2026-09-01T00:00:00Z

Historical holdout:
2026-09-01 through 2026-09-30 — LOCKED / MUST NOT BE FETCHED.

## Discovery gate

Illustrative payout reference:
80%.

Break-even accuracy reference:
55.5555556%.

Cell eligibility:
- N >= 120 for 10m;
- N >= 100 for 30m;
- N >= 80 for 60m;
- N >= 40 for 1d;
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- accuracy > 50% in each chronological discovery third.

Eligible cells receive a one-sided exact binomial p-value vs p0=55.5555556%.

Apply Benjamini-Hochberg FDR q=0.05 across the entire V0.5 eligible family.

Only BH-selected cells may open August OOS.

## OOS gate

Without changing leader, target, lookback, horizon or mode:
- point accuracy > 55.5555556%;
- Wilson 95% lower bound > 50%;
- one-sided exact binomial p-value vs 55.5555556% < 0.05;
- EV under illustrative 80% payout > 0.

Any survivor = PROXY CANDIDATE only.

## Hard boundaries

- No September 2026 data.
- No exact Event Futures profitability claim.
- No historical 80% payout assumption presented as fact.
- No live trading.
- No authenticated exchange requests.
- No account mutation.
- No merge to main.
