# ORDERBOOK-RESILIENCE-001 — PRE-SOURCE AUTHORITY V0.1

Status: **FROZEN / SOURCE-ONLY / OUTCOME-BLIND**  
Date: **2026-09-17**  
Branch: `orderbook-resilience-v0.1`

## Hypothesis family

Primary: MICRO.

Economic mechanism under consideration: after a local liquidity/depth shock, market-maker replenishment speed may distinguish absorbed impact from persistent depleted-liquidity states.

This is not a raw taker-imbalance or OI predictor. The candidate state variable is **liquidity resilience/replenishment after depletion**.

## Source question only

Before defining any predictor, event shock, horizon, direction or outcome, determine whether Binance USD-M Futures public `bookDepth` archives contain data granular enough to identify replenishment rather than merely coarse depth regime.

Canonical source candidate:
`data.binance.vision/data/futures/um/daily/bookDepth/BTCUSDT/`

Protected source window for feasibility: selected deterministic dates in 2023-2024 only. 2025/2026 forbidden.

Probe dates frozen before reading file contents:
- 2023-01-01
- 2023-06-15
- 2024-01-15
- 2024-12-15

## Fields allowed at source probe

May inspect only:
- archive existence/status/size/checksum;
- CSV header/schema;
- timestamp column;
- structural depth-band label (`percentage`) if present;
- row counts and rows-per-snapshot;
- unique snapshot timestamps and cadence/gap diagnostics.

Forbidden:
- depth amounts;
- notional amounts;
- price series;
- returns;
- future impact;
- direction;
- PnL/win rate/PF/drawdown;
- any 2025/2026 data.

## Prospectively frozen adequacy gate

For the specific mechanism **order-book replenishment/refill after shock**, the source must support both:
1. near-market depth state at sufficiently fine temporal resolution; and
2. repeated snapshots fast enough to estimate a refill trajectory on a 5-minute or shorter mechanism horizon without claiming sub-snapshot latency.

V0.1 minimum temporal adequacy: median unique-snapshot interval **<= 5 seconds** on every probe file, with p95 interval <= 10 seconds.

A source that reports only broad percentage bands around mid rather than reconstructable near-touch/L2 depth is classified `SOURCE_SEMANTICS_TOO_COARSE_FOR_TRUE_REFILL`, even if files are otherwise complete.

A ~30-second aggregate percentage-band archive therefore must NOT be rescued by changing the mechanism to generic depth imbalance under this LAB_ID.

Permitted source-stage results:
- `SOURCE_SCHEMA_PASS`
- `SOURCE_TEMPORAL_RESOLUTION_FAIL`
- `SOURCE_SEMANTICS_TOO_COARSE_FOR_TRUE_REFILL`
- `SOURCE_ACQUISITION_TECHNICAL_FAILURE`
- `PROVENANCE_FAILURE`

No result at this phase is an edge verdict.
