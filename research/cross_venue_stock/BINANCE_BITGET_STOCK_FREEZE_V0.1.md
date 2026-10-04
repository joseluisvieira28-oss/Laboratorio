# BINANCE ↔ BITGET STOCK LEAD-LAG V0.1 — PRE-OUTCOME FREEZE

Date: 2026-10-05
Status: FROZEN BEFORE OUTCOMES

## Source authority
Source-only run: `37238930919`
Source artifact SHA256: `6300d91d8b7bdef8c201e1589e8f35a29e660f192ca7a99969374ea767b01d43`
Burned source date: 2026-08-14.

34 assets have complete Binance + Bitget transport on the burned source date.
PDDUSDT is excluded solely because Binance source transport failed on that date.

## Untouched outcome window
2026-08-17 through 2026-09-04 inclusive.
Expected weekdays: 15.

This window is distinct from the MEXC V0.5 September/October outcome window.

## Two routes
Every asset is tested in BOTH directions:
1. Bitget leader → Binance target
2. Binance leader → Bitget target

No route may be removed after outcomes.

## Frozen signal
- leader 1m shock >= 5 bps
- lag gap = leader 1m return - target 1m return
- sign(lag gap) must equal sign(leader return)
- abs(lag gap) >= 3 bps
- direction = FOLLOW_LEADER
- horizon = 1 minute
- cooldown = 1 minute
- exact closed-candle timestamps
- no forward fill or interpolation

## Scientific gate
Per asset-route:
- N >= 50
- >= 10 distinct signal sessions
- mean gross > 0
- median gross > 0
- win rate > 50%
- all three chronological thirds mean > 0
- exact one-sided binomial p
- Holm-Bonferroni FWER 0.05 across all 68 tests.

## Frozen execution costs
Binance TradFi target:
- maker-maker 0 bps
- maker-taker 4 bps
- taker-taker 8 bps

Bitget target:
- maker-maker 4 bps
- maker-taker 8 bps
- taker-taker 12 bps

An immediate-execution candidate must survive the target venue's taker-taker fee scenario after scientific PASS.

A hybrid candidate must survive maker-taker fees.
A maker-only candidate must survive maker-maker fees.

None of these classifications grants live trading authority. Spread, slippage, latency, fill probability and forward validation remain separate.

No per-asset threshold tuning, route-specific threshold tuning, retrospective rescue, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
