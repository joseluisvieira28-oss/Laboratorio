# LCOD-001 PREDICTOR-ONLY VIABILITY REVIEW FREEZE V0.1

Frozen: 2026-09-26
Lab: LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001
Parent authority: LCOD_PROSPECTIVE_MECHANICAL_STATE_OBSERVATION_FREEZE_V0.1
Stage: M2 FORWARD MECHANISM / OUTCOME-BLIND
Current series at freeze: 2 canonical observations across 2 UTC days.

## Purpose

Pre-register the exact predictor-only review that may run once the existing accumulation gate is met.

This document does NOT open outcomes and does NOT define a trading signal.

The review may execute only when BOTH are true:
- canonical successful daily observations >= 30;
- distinct UTC days >= 21.

Until then its status is ACCUMULATION_GATE_NOT_READY.

## Inputs

Only durable canonical LCOD forward snapshots and the forward-series index are authorized.

Forbidden inputs:
- market returns;
- liquidation-event outcomes after each snapshot;
- direction labels;
- PnL;
- execution data;
- exchange data used as an outcome;
- any manually selected subset of dates or shock points.

## Frozen review dimensions

All calculations use the full canonical series. No date may be dropped because it looks unusual if it already passed the frozen snapshot gates.

### 1. Source / provenance stability

Report:
- canonical observation count;
- distinct UTC day count;
- duplicate count;
- boundary-violation count;
- diagnostic/noncanonical file count;
- unique scientific-code SHAs;
- unique workflow event names;
- count of snapshots with full component coverage;
- count of snapshots with zero decode/UAD errors.

No edge interpretation is permitted.

### 2. Active population variation

Across every canonical observation report for active_debt_pair_count:
- minimum;
- maximum;
- arithmetic mean;
- population standard deviation;
- first-to-last change;
- consecutive absolute change mean;
- consecutive absolute change maximum.

No borrower identities are retained or opened.

### 3. Total active debt variation

Across every canonical observation report total_active_debt_value_ray:
- minimum;
- maximum;
- arithmetic mean;
- population standard deviation;
- first-to-last relative change;
- consecutive absolute relative-change mean;
- consecutive absolute relative-change maximum.

This is descriptive only.

### 4. Full nine-point curve variation

The entire frozen vector MUST be evaluated.

For every stress point in:
0, 25, 50, 75, 100, 150, 200, 300, 500 bps

report separately for:
- cumulative_new_count;
- cumulative_new_debt_value_ray;
- cumulative_new_debt_value_ray / total_active_debt_value_ray.

For each coordinate report:
- minimum;
- maximum;
- arithmetic mean;
- population standard deviation.

No single shock point may be declared primary based on this review.

### 5. Full-vector day-to-day movement

For each consecutive canonical observation pair compute, over ALL nine shock points:
- L1 distance of the cumulative debt-fraction vector;
- L2 distance of the cumulative debt-fraction vector;
- maximum absolute coordinate movement.

Report min/max/mean/population-standard-deviation for each distance family.

No outcome is consulted.

### 6. Slope and curvature variation

Use every stored interval slope and every stored interior curvature coordinate.

For each slope coordinate and each curvature coordinate report:
- minimum;
- maximum;
- arithmetic mean;
- population standard deviation.

Fractions are evaluated from their exact stored numerator/denominator values.

No coordinate selection or ranking is authorized.

## Missingness / integrity rules

The review is fail-closed.

It may not complete if any canonical snapshot:
- lacks the full nine-point grid;
- lacks total active debt;
- lacks active population count;
- lacks curve SHA;
- lacks workflow scientific-code SHA;
- has market_returns_opened != false;
- has future_liquidation_outcomes_opened != false;
- has pnl_opened != false;
- has mutation != false;
- contains a stress grid different from the frozen nine-point grid.

No imputation is permitted.

## Allowed classifications

Before gate:
ACCUMULATION_GATE_NOT_READY

At/after gate, if integrity checks fail:
PREDICTOR_ONLY_REVIEW_BLOCKED

At/after gate, if integrity checks pass:
PREDICTOR_ONLY_REVIEW_COMPLETE

PREDICTOR_ONLY_REVIEW_COMPLETE is NOT evidence of predictive edge.
It earns zero promotion credit.

## Next-stage firewall

Only after PREDICTOR_ONLY_REVIEW_COMPLETE may a separate future document pre-register:
- predictor transform(s);
- outcome definition(s);
- horizon(s);
- discovery/OOS/holdout boundaries.

Those later definitions MUST be frozen before outcomes are opened.

This freeze does not authorize:
- outcome inspection;
- parameter fitting;
- shock-point selection;
- direction selection;
- threshold tuning;
- PnL;
- live trading;
- merge of scientific PR #91 to main.
