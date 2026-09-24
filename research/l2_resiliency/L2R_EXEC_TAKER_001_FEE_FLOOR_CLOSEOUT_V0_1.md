# L2R-EXEC-TAKER-001 — DIRECT TAKER FEE-FLOOR CLOSEOUT V0.1

Date: 2026-09-24  
Status: **DIRECT STANDARD-BASE TAKER ROUTE ECONOMICALLY INFEASIBLE / CHILD ROUTE CLOSED**  
Parent mechanism: `L2-RESILIENCY-001` remains `VALIDATION_PASS`.

## Frozen executable child

WEAK-only continuation, same six parent cells, Hyperliquid BTC perpetual, marketable entry at R and marketable exit at Y.

This is a new execution child. It does not rewrite parent science.

## Fee-floor argument

Official Hyperliquid current base perp fee:
- taker = **4.5 bps per fill**;
- round trip = **9.0 bps** before spread/slippage.

Official source:
https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees

Observed 2025 WEAK event-level midpoint means across the six parent cells:
- R1_Y5: +0.9212709451 bps
- R1_Y15: +1.2438948381 bps
- R1_Y60: +1.3442512507 bps
- R5_Y15: +1.0523175586 bps
- R5_Y60: +1.2155079252 bps
- R15_Y60: +1.1160779274 bps

The most favorable observed WEAK midpoint mean is therefore +1.3442512507 bps.

A marketable-touch return cannot exceed the same event's midpoint-to-midpoint continuation after accounting for crossing the spread on entry and exit. Therefore the current standard-base taker route has an upper fee-floor bound no better than:

`+1.3442512507 - 9.0 = -7.6557487493 bps/opportunity`

before additional slippage, latency, depth impact or missed timing.

## Adjudication

`DIRECT_STANDARD_BASE_TAKER_FEE_FLOOR_FAIL`

No full taker backtest is required to establish that the current standard-base route cannot monetize an approximately 1 bps short-horizon midpoint effect with a 9 bps fee-only round trip.

This is an **execution-path failure**, not `NO_EDGE` for the parent mechanism.

No rescue by selecting a favorable cell, reducing fees after outcome, changing horizon, direction, venue, threshold or subperiod is permitted under this child identity.

A discounted/institutional fee route would require a separately frozen account-specific execution envelope before evidence is opened.

## MEXC API note

MEXC announced API Futures fees effective 2026-06-01 of 6 bps maker and 8 bps taker per fill. That automatic execution path is even less compatible with this ~1 bps parent effect and is not adopted as the direct child venue.

Source:
https://www.mexc.com/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742

No cross-venue hypothesis is tested or rejected here.
