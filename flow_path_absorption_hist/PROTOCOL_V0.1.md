# FLOW-PATH-ABSORPTION-HIST-001 — Historical Core Mechanism Test V0.1

Status: FROZEN PRE-OUTCOME / RESEARCH ONLY
Branch: flow-path-absorption-hist-v0.1
Frozen before historical future returns are opened.

## Purpose
Fast historical test of the economic core behind absorption vs efficient acceptance using only official Binance BTCUSDT 1m klines.

This is a separate identity from ABSORPTION-FAILED-AUCTION-001. It does not backfill, modify, or rescue the prospective child.

## Source
Official public Binance Vision Spot BTCUSDT 1m monthly kline archives, each verified against its official .CHECKSUM.

Each 1m row provides:
- OHLC
- base volume
- taker buy base volume

For a UTC-aligned 5m bar:
- base_volume = sum of five 1m base volumes
- aggressive_buy = sum taker buy base volume
- aggressive_sell = base_volume - aggressive_buy
- delta_pct = (aggressive_buy - aggressive_sell) / base_volume

Exactly five 1m bars are required.

## Frozen structural features
LTF path efficiency is identical in form to MM-V1:
path = |close_1-open_1| + |close_2-close_1| + ... + |close_5-close_4|
net = |close_5-open_1|
efficiency = net/path for path>0.

bar_return_bps = (close_5/open_1 - 1) * 10000.

No POC, VA or imbalance field is used in this lab. This deliberately isolates the core question:
does extreme aggressor flow with inefficient/weak price response reverse, while extreme flow with efficient aligned price response continue?

## Frozen classifier
Rolling baseline: prior 2,016 valid 5m bars.

At each evaluable bar:
- extreme flow: abs(delta_pct) >= rolling q95 AND base_volume >= rolling q75;
- low efficiency: path_efficiency <= rolling q25;
- high efficiency: path_efficiency >= rolling q75;
- low displacement threshold: rolling q25 of abs(bar_return_bps);
- d = sign(delta_pct).

FAILED_AUCTION:
- extreme;
- low efficiency;
- d*bar_return_bps <= 0 OR abs(bar_return_bps) <= rolling q25 abs return.

EFFICIENT_ACCEPTANCE:
- extreme;
- high efficiency;
- d*bar_return_bps > 0.

Other extreme bars = UNCLASSIFIED_EXTREME.
Cooldown after accepted primary event = 12 bars / 60 minutes.
Cooldown-suppressed candidates do not enter primary groups.

## Outcomes
Outcome clock starts at event-bar close.

For H in {5,15,30,60,240} minutes:
R_H = d * (close_T+H / close_T0 - 1) * 10000.

Positive = continuation in aggressor direction.
Negative = reversal against aggressor direction.

Primary horizon = R60.

## Frozen split
DISCOVERY:
- warmup: 2022-12
- evaluable window: 2023-01-01 through 2024-12-31 UTC.

OOS:
- opened only if Discovery = MECHANISM_SURVIVES;
- warmup: 2024-12
- evaluable window: 2025-01-01 through 2025-12-31 UTC.

No threshold, feature, event, outcome, cooldown, source or adjudication change is allowed between Discovery and OOS.

## Minimum evidence per phase
- >=100 FAILED_AUCTION
- >=100 EFFICIENT_ACCEPTANCE
- >=30 distinct UTC event dates
- >=99% valid 5m source coverage
- >=99% R60 outcome coverage in each primary group
- zero unresolved source conflicts

Otherwise: INSUFFICIENT_SAMPLE or SOURCE_BLOCKED.

## Primary gate
MECHANISM_SURVIVES requires ALL:
1. median FAILED_AUCTION R60 < 0
2. median EFFICIENT_ACCEPTANCE R60 > 0
3. median contrast EA - FA > 0
4. deterministic event-level bootstrap 95% CI lower bound >0
5. FAILED_AUCTION reversal rate >50% and Wilson 95% lower bound >50%
6. EFFICIENT_ACCEPTANCE continuation rate >50% and Wilson 95% lower bound >50%

Bootstrap: 10,000 resamples, seed 20260924.

Discovery failure stops before OOS.
Discovery survive + OOS fail => OOS_FAILED.
Discovery survive + OOS survive => OOS_REPLICATED_MECHANISM.

## Anti-rescue
After Discovery opens:
- no quantile change
- no baseline change
- no cooldown change
- no horizon change
- no session/volatility/side/date filtering
- no lag shift
- no source swap
- no subgroup rescue
- no alternative return definition

A changed design requires a new lab ID.

## Authority
Research only.
No live trading.
No order placement.
No exchange mutation.
No merge to main.
No promotion from this test alone.
Trading authority: NONE.
