# ORDERBOOK-RESILIENCE-001 — SOURCE CLOSEOUT V0.1

Date: 2026-09-17  
Branch: `orderbook-resilience-v0.1`

## Verdict

**SOURCE_TEMPORAL_RESOLUTION_FAIL**

This is a source/mechanism-fit verdict, not an economic-performance verdict and not `NO_EDGE`.

The frozen candidate was **true liquidity replenishment/resilience after depletion**. The official Binance USD-M `bookDepth` archive is not sufficiently granular for that mechanism under the prospectively frozen V0.1 gate.

## Frozen probes

All four deterministic protected-safe probe files returned HTTP 200 and the same schema:

`timestamp, percentage, depth, notional`

Dates:
- 2023-01-01
- 2023-06-15
- 2024-01-15
- 2024-12-15

Observed structural cadence, without opening depth/notional values:
- 2023-01-01 median = 29s; p95 = 37s
- 2023-06-15 median = 30s; p95 = 35s
- 2024-01-15 median = 29s; p95 = 36s
- 2024-12-15 median = 30s; p95 = 32s

Each snapshot contains exactly ten structural percentage bands: `-5,-4,-3,-2,-1,+1,+2,+3,+4,+5` percent. This is aggregated band-depth data, not reconstructable near-touch L2 state.

Frozen V0.1 minimum for the stated refill mechanism was median <=5s and p95 <=10s, plus sufficiently near-market semantics. The temporal gate fails decisively, and the broad percentage-band schema independently confirms that this source should not be represented as true L2 replenishment.

## Safety receipt

GitHub Actions run: `35214348735`  
Artifact: `10494103585`  
Artifact SHA256: `5598281799ca6e9167372c68bb4c62f1e41c37a493cbaff4b5219cf87cdf2507`

No depth or notional values were parsed. No price series, future impact, returns, PnL, win rate, PF or drawdown was opened. No 2025/2026 data was accessed. No exchange/wallet mutation or live trading occurred.

## Scientific consequence

STOP this LAB_ID for **true order-book refill/resilience using public Binance `bookDepth` archives**.

Do not rescue by:
- lengthening the horizon after seeing this source;
- relabelling 30-second percentage-band depth as L2 refill;
- changing to a generic depth-regime/imbalance hypothesis under the same LAB_ID;
- opening outcomes anyway.

A future lab using a genuinely independent full-depth/high-frequency historical source would require a new pre-source authority and a new source gate. A separate generic depth-regime mechanism, if ever justified economically, is also a new hypothesis rather than a continuation of this one.
