# CBETH-REDEMPTION-BASIS-001 — MECHANISM SAMPLE BOUNDARY ADDENDUM V0.1A

Frozen: 2026-09-27
Parent: PRE_OUTCOME_PREDICTOR_DESIGN_FREEZE_V0.1
Timing: BEFORE source-gate execution and before all predictor/outcome data.

## Purpose

Prevent end-of-Discovery boundary censoring from silently reducing the mechanism sample below the already-frozen scientific minimum.

## Frozen mechanism-eligible sample

Discovery predictor sample gate is evaluated on all:
2024-07-01 through 2024-12-31.

The 12-day primary mechanism outcome is eligible only for entry dates:
2024-07-01 through 2024-12-19 inclusive.

After applying only this pre-frozen calendar boundary, MECHANISM_SAMPLE_PASS requires:
- >=20 eligible transition events total;
- >=6 eligible DISCOUNT_EXTREME events;
- >=6 eligible PREMIUM_EXTREME events.

If the predictor sample gate passes but boundary censoring leaves fewer than these counts:
MECHANISM_OUTCOME_INSUFFICIENT_SAMPLE.

No outcome statistic is computed in that state.

No threshold, horizon, tail, date window or de-clustering rescue is allowed.

The 3-day diagnostic cannot add primary-eligible events or rescue the 12-day sample.

OOS 2025 and protected 2026 remain CLOSED.
