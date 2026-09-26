# XVEN-DISLOC-001 — FORWARD OBSERVATION FREEZE V0.1

Date: 2026-09-26
Status: PRE-FORWARD FREEZE

## Purpose
Determine the natural distribution and persistence of public Binance↔MEXC executable BBO dislocations without trading.

## No strategy threshold
This observer records the distribution. It does not trigger trades.

## Capture unit
Every time either venue updates and both venues are fresh:
- local monotonic timestamp
- both BBOs
- age of each venue quote
- executable gap in both directions
- maximum executable gap
- which direction is larger

Stale limit: 1,000 ms.

## Fixed descriptive bins
For reporting only, not trading:
- > 1 bps
- > 2 bps
- > 5 bps
- > 10 bps
- > 12 bps
- > 16 bps
- > 20 bps

These correspond to descriptive magnitude levels including current maker/taker fee hurdles; they are not optimized thresholds.

## Episode rule
A gap episode starts when max executable gap > 1 bps and ends when it returns <= 1 bps or either venue becomes stale.

For each episode preserve:
- start/end monotonic time
- duration
- peak executable gap
- direction
- number of paired updates

## First observation horizon
10 minutes per workflow run.

No live trading.
No exchange authentication.
No exchange mutation.
No OOS/holdout concept applies to this forward source observer.
