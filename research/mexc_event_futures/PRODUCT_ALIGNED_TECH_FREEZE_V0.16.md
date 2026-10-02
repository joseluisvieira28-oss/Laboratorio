# MEXC EVENT FUTURES LAB — PRODUCT-ALIGNED TECHNICAL REBUILD FREEZE V0.16

Date: 2026-10-02
Status: PRE-OUTCOME / SOURCE-DRIVEN ECONOMIC CORRECTION / FAIL-CLOSED

## Why V0.16 exists

Exact anonymous Event Futures product data discovered after V0.4 showed two material source facts that were not known when the earlier technical family was frozen:

1. the currently ONLINE product horizon differs by asset class;
2. payout is horizon-specific and dynamic.

No individual V0.4 cell metrics were inspected during this correction; only aggregate pass counts were used.

## Exact current online universe

ONLINE:
- BTC_USDT
- ETH_USDT
- NVIDIA_USDT
- SPCXSTOCK_USDT
- MUSTOCK_USDT

OFFLINE records are excluded:
SOL_USDT, XRP_USDT, SUI_USDT, DOGE_USDT.

## Frozen product horizons and payout reference

This is the exact public product snapshot captured in V0.12.2 on 2026-10-02.

BTC_USDT:
- 10m: 0.80
- 30m: 0.85
- 60m: 0.85
- 1440m: 0.85

ETH_USDT:
- 10m: 0.40
- 30m: 0.85
- 60m: 0.85
- 1440m: 0.85

NVIDIA_USDT / SPCXSTOCK_USDT / MUSTOCK_USDT:
- 10m: 0.80
- 30m: 0.85
- 60m: 0.85
- 240m: 0.85

IMPORTANT:
These payouts are a CURRENT REFERENCE, not historical truth. V0.14 prospective monitoring is separately measuring payout variation.

## Source binding

V0.15 proved the anonymous Event Futures page itself loads:
- `/event_contract/detail`;
- `/contract/ticker?` with BTC_USDT `indexPrice`;
- `/contract/kline/index_price/BTC_USDT`.

Therefore the standard futures index-price K-line source used by this study is directly bound to the Event Futures page chart source.

This still does not prove byte-for-byte settlement tick semantics.

## Frozen technical strategies

Same V0.4 strategy definitions and parameters, unchanged:
- EMA_TREND_9_21
- RSI14_EXTREME_REV
- DONCHIAN20_BREAKOUT
- BOLL20_2_REV
- STREAK3_REV
- STREAK3_CONT
- ROC3_CONT
- RANGE20_POSITION_REV

Chart timeframes:
5m, 15m, 60m, 240m, 1440m.

No new indicator or parameter tuning.

## Partitions

Discovery:
2026-04-01 <= t < 2026-08-01 UTC

OOS:
2026-08-01 <= t < 2026-09-01 UTC

September 2026:
LOCKED / NOT FETCHED.

## Product-aligned economic null

For each asset/horizon with frozen payout q:

`break_even_accuracy = 1 / (1 + q)`

Examples:
- q=0.40 => 71.4286%
- q=0.80 => 55.5556%
- q=0.85 => 54.0541%

## Discovery gate

Minimum non-tie N:
- 10m >= 120
- 30m >= 100
- 60m >= 80
- 240m >= 50
- 1440m >= 40

Cell eligible only if:
- point accuracy > its product-aligned break-even accuracy;
- Wilson 95% lower bound > 50%;
- accuracy > 50% in each discovery third;
- one-sided exact binomial p-value vs its own break-even null is computable.

Apply Benjamini-Hochberg FDR q=0.05 across the entire eligible V0.16 family.

Only BH-selected cells may open August OOS.

## OOS gate

No parameter changes.

Pass only if:
- accuracy > frozen product-aligned break-even;
- Wilson 95% lower bound > 50%;
- one-sided exact binomial p < 0.05 vs that break-even;
- unit EV using the frozen current-reference payout > 0.

Any survivor is:
**CURRENT-PAYOUT-REFERENCE PROXY CANDIDATE ONLY**.

It is NOT historical exact Event Futures profitability and cannot be promoted to live trading without prospective payout/settlement validation.

## Hard boundaries

No September holdout.
No live trading.
No orders.
No account mutation.
No historical payout fabrication.
No main merge.
