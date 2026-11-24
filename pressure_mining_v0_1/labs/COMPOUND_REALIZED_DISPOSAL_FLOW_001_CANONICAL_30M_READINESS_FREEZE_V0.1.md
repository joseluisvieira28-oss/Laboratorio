# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — CANONICAL 30M PREDICTOR READINESS FREEZE V0.1

Date: 2026-09-28
Status: SOURCE-ONLY / CANONICAL 30M CONTRACT CHECK

Purpose:
verify, without market outcomes, that the exact predictor population implied by the canonical protected 2025 30-minute Economic Discovery V0.1 can satisfy its frozen sample gates after its deterministic event aggregation and overlap suppression.

Allowed:
BuyCollateral source logs, event transaction hash, asset, baseAmount, collateralAmount, block timestamp.

Forbidden:
BTC/ETH/LINK/UNI/COMP price values, returns, PnL, funding, basis, volatility, post-event market outcomes.

Exact included assets:
- WETH -> ETHUSDT
- LINK -> LINKUSDT
- UNI -> UNIUSDT
- COMP -> COMPUSDT

Exact event construction:
1. aggregate all BuyCollateral logs sharing the same transaction hash and collateral asset;
2. T0 = transaction block timestamp;
3. sort by mapped asset then T0;
4. keep first event per asset;
5. suppress later same-asset events with T0 < kept T0 + 30 minutes;
6. resume eligibility at or after the 30-minute boundary;
7. cross-asset events may coexist.

Frozen readiness gates copied from canonical economic contract:
- N >= 100;
- >=20 unique ISO weeks;
- each of all four assets has >=10 events.

Readiness PASS does not open outcomes and does not establish edge.
