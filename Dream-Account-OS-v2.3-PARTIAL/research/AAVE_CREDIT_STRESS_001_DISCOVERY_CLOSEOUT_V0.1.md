# AAVE-CREDIT-STRESS-001 — REGRESSION DISCOVERY CLOSEOUT V0.1

Date: 2026-09-18
Discovery ID: AAVE-CS001-REGRESSION-DISCOVERY-001
Canonical run: 35334070486
Canonical head: 2cdd51950d058e2bc670196ba86a612abf571797

## FINAL CLASSIFICATION

DISCOVERY_NO_PREDICTIVE_CREDIT_EDGE

## FROZEN RESULT

- regression rows: 703
- nonzero predictor rows: 703
- unique UTC week blocks: 102
- full-sample beta: +0.0000262303751 BTC log-return per +1 percentage-point daily Aave USDC variable-borrow-rate change
- beta 2023: +0.0000352004918
- beta 2024: +0.0000253977055
- week-block bootstrap fraction beta >= 0: 60.42%
- bootstrap 95th percentile beta: +0.000206881
- HAC/Newey-West lag-7 one-sided p(beta < 0): 0.59524
- HAC t-stat: +0.2410

All sample gates passed. Every directional/predictive promotion gate failed.

## INTERPRETATION

The prospectively frozen hypothesis required beta < 0: tighter Aave USDC borrowing conditions should precede weaker next-day BTC. The observed coefficient was positive in the full sample and in both calendar years, with no statistical support for the frozen negative sign.

## NO RESCUE

Do not invert the sign, threshold rate shocks, select only positive/negative changes, switch reserve, change horizon, remove governance/IRM dates, add regime filters, change bootstrap/HAC settings, open 2025, or create a trading rule under this Discovery ID.

The exact AAVE-CREDIT-STRESS-001 MVE is scientifically closed.

2025/2026 accessed: false
PnL: false
Live trading / exchange mutation / wallet access / main merge: false
