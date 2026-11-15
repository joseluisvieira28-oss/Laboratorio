# LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001

Status: M2 SOURCE GATE / PRE-OUTCOME
Opened: 2026-09-24
Primary family: CREDIT
Secondary family: MICRO

## Distinct causal identity

This lab is NOT:
- AAVE-LIQUIDATION-OVERHANG-001 (closed after 2024 replication no-signal);
- AAVE-HF-CROWDING-001 (active outcome-blind calibration of borrower HF<1.10 crowding);
- DEFI-LIQUIDATION-SHOCK-001 (historical liquidation-event source gate).

The new object is a price-shock response curve:

oracle shock -> position revaluation -> debt newly eligible for liquidation -> convexity / acceleration

It asks where the liquidation-eligible inventory changes non-linearly as oracle prices move, before any downstream market return is opened.

## Mechanism

Aave liquidation eligibility begins when borrower health factor falls below 1. Health factor depends on collateral values, liquidation thresholds and debt. Therefore a fixed borrower census plus protocol parameters and oracle prices defines a deterministic local solvency surface.

The hypothesis is NOT that low HF alone predicts BTC.
The hypothesis is that the *slope and curvature* of newly liquidatable debt across small price shocks may define a mechanically fragile state that can later be tested jointly with market crowding/liquidity.

## Governance

- Source/mechanism only.
- No BTC/ETH return, markout, PnL or direction is opened in V0.1.
- No liquidation transaction submission.
- No wallet/exchange mutation.
- No parameter or shock-grid rescue after outcome inspection.
- No merge to main without explicit authorization.
