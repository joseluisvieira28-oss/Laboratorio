# DEFI-LIQUIDATION-SHOCK-001 — PRE-DISCOVERY TEMPORAL HOLDOUT FREEZE V0.1

Date: 2026-09-27
Status: FROZEN / OUTCOME-BLIND / PROSPECTIVE

## Purpose

Freeze the temporal experimental split before any market outcome is opened.

## Frozen split

### Discovery
All otherwise-authorized source events/clusters with T0 strictly before:
`2024-01-01T00:00:00Z`

and at or after each protocol/class's frozen source lower boundary.

### OOS
All otherwise-authorized source events/clusters with:
`2024-01-01T00:00:00Z <= T0 < 2025-01-01T00:00:00Z`

No Discovery tuning may use 2024 outcomes.

### Protected holdout
All 2025 and 2026 market outcomes remain CLOSED.

They are not OOS for this first experiment and may not be opened to rescue, select, tune or promote a weak 2021–2024 result.

## Late-launch families

A protocol/class whose first authoritative source event occurs in 2024 has no Discovery observations.

Such a family is:
`EXTERNAL_CONFIRMATORY_ONLY`

It may be evaluated only under rules frozen using source information and, where applicable, Discovery rules established without its 2024 market outcomes.

It cannot be used to tune horizons, controls, direction logic, thresholds or statistical tests.

## Boundary rule

Cluster/event membership is assigned from source timestamps only.

If a source cascade crosses 2023-12-31 / 2024-01-01:
- its final T0 determines the split;
- it is never divided using market outcomes.

If a cluster would cross 2024-12-31 / 2025-01-01:
- it is excluded from the 2021–2024 experiment rather than opening any protected 2025 outcome.

## No rescue

Discovery failure cannot be rescued by redefining the split.
OOS failure cannot be rescued by opening 2025/2026.
Any later protected-holdout authority requires a new explicit frozen gate.

## Firewall

prices=false
returns=false
pnl=false
economic_outcomes=false
protected_2025_2026_market_outcomes=false
post_outcome_tuning=false
live_trading=false
merge_main=false
