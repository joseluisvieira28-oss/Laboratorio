# LIQUIDATION-PRESSURE-002-FORWARD — ENGINE IMPLEMENTATION FREEZE V0.1

**Frozen:** 2026-09-23 before canonical q95 calibration and before any liquidation-return markout  
**Authority:** ECONOMIC_MVE_FREEZE_V0.1  
**MVE:** LP2-BYBIT-REV5S-Q95-H30-V1

## Purpose

Lock the transformation from prospectively calibrated liquidation bursts to shadow execution outcomes before real economic outcomes are opened.

## Data boundary

The engine refuses to run unless the supplied threshold receipt has `canonical_thresholds_emitted=true` and verdict `SOURCE_CALIBRATION_PASS_READY_TO_FREEZE`.

The threshold receipt `generated_at_utc` is the hard forward boundary. Any raw message received before that timestamp is excluded from economic Discovery.

## Event state machine

1. Parse Bybit `allLiquidation` records into frozen non-overlapping 5-second exchange-time windows.
2. A symbol is eligible only when its canonical source-only q95 threshold is non-null.
3. Candidate burst: total liquidation notional >= frozen per-symbol q95 and net forced direction != 0.
4. `S=Buy` contributes long-liquidation / forced-sell notional; `S=Sell` contributes short-liquidation / forced-buy notional.
5. Reversal direction only: net forced sell => LONG; net forced buy => SHORT.
6. Entry is the first valid reconstructed L2 book whose exchange timestamp is >= burst close.
7. Exit target is exactly entry book timestamp + 30,000 ms; exit is the first valid reconstructed book at or after that target.
8. While an event is active, later candidate bursts in the same symbol are not independent.
9. After exit, same-symbol cooldown continues for 60,000 ms. Any candidate burst before cooldown end is excluded from independent-event count.

## Book reconstruction

Use Bybit orderbook.50 snapshot/delta messages in raw arrival order. Snapshot replaces the book. Delta updates price levels; zero quantity deletes a level. Invalid/crossed books are fail-closed and cannot generate execution.

Use `data.cts` where present, otherwise top-level `ts`, as exchange book time. No interpolation and no future book may be used before its timestamp.

## Funding exclusion

Use latest prospectively received public `tickers.{symbol}` metadata at entry. If `nextFundingTime` is > entry exchange timestamp and <= exit target, exclude the event. Missing funding metadata => event unavailable, not zero funding cost.

## Execution

Frozen notionals: 100, 500, 1,000 and 5,000 USDT.

LONG:
- entry consumes asks until exact quote notional is spent;
- exit sells the exact acquired base quantity into bids.

SHORT:
- entry sells enough base into bids to reach exact quote notional;
- exit buys back the exact base quantity from asks.

Insufficient visible top-50 depth on either side => that notional/event is unavailable.

## Costs

BASE: 5.5 bps taker fee on each executed leg.  
STRESS: 10 bps taker fee on each executed leg.

Observed spread and level-by-level depth slippage are intrinsic to the execution simulation. No maker rebate, no fee discount and no post-outcome fee substitution.

## Statistics

For each notional and cost regime report count, total net USDT, mean/median net bps, positive-event rate, per-symbol mean, positive-PnL concentration by symbol/day, and top-1%-event positive-PnL share.

Primary uncertainty test: nonparametric **UTC-day cluster bootstrap**, 10,000 resamples, fixed seed `260923`. Resample observed UTC days with replacement; include all events from each sampled day; lower 95% bound = 2.5th percentile of bootstrap mean net bps.

## Adjudication

The engine must return `INSUFFICIENT_FORWARD_SAMPLE` unless the MVE sample gates are met. It may emit `SURVIVES_DISCOVERY` only when every frozen survival gate passes. Any valid full-sample failure returns `NO_EDGE` for this exact MVE. No continuation, horizon, q-level, symbol or notional rescue is permitted under this ID.

## Safety

Read-only public market data. No API key, account endpoint, order, wallet, leverage setting or exchange mutation.
