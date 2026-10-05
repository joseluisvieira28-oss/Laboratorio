# LIQUID CO-INVEST FORWARD — CONFIRMATORY DECISION FREEZE V0.1

Date: 2026-10-05
Branch: liquid-coinvest-forward-v0.1-prereg-2026-10-05
Status: ACTIVE / FROZEN BEFORE ANY SUCCESSFUL OUTCOME RECEIPT

## Purpose
Prevent optional stopping, threshold fishing, horizon switching and post-outcome rescue.

## Confirmatory population
Only EVENT_ELIGIBLE proprietary source advances count. BASELINE_ONLY, DUPLICATE_SOURCE_SNAPSHOT, SOURCE_TIMESTAMP_ONLY and SOURCE_INTEGRITY_CONFLICT do not count as independent confirmatory events.

A source-version cluster groups EVENT_ELIGIBLE rows whose source_created_at_utc timestamps are within 5 seconds.

## Fixed readiness gate
No terminal edge verdict until all conditions hold:
- at least 60 unique source-version clusters;
- at least 7 distinct UTC dates;
- at least 150 EVENT_ELIGIBLE symbol rows;
- BTC, ETH and SOL each contribute at least 40 EVENT_ELIGIBLE rows;
- at least 95% of eligible primary-horizon outcomes are canonically resolved;
- zero unresolved SOURCE_INTEGRITY_CONFLICT rows;
- forward-receipt and outcome validators pass.

Before this gate: FORWARD_INSUFFICIENT. No early stopping on interim performance.

## LIQUIDATION-FLOW-FWD-001-LIQUID-V0.1
Primary predictor: liq_near_total_usd / total_positioning_usd.
Primary outcome: +1h absolute_return_pct.
Secondary robustness outcome: +4h absolute_return_pct.

Frozen hypothesis: higher liquidation-near exposure predicts larger subsequent absolute price movement.

Primary analysis:
- within-symbol predictor ranks;
- pooled Spearman correlation with +1h absolute return;
- source-only nearest-rank Q4 minus Q1 mean +1h absolute return;
- leave-one-UTC-date-out sign checks.

SURVIVES_FORWARD requires:
- primary Spearman rho > 0;
- Q4 minus Q1 > 0;
- at least 75% of leave-one-date-out folds preserve each positive sign;
- +4h Spearman sign non-negative;
- no single UTC date contributes more than 40% of total Q4-Q1 numerator magnitude.

Otherwise: NO_EDGE.

## COHORT-DIVERGENCE-FWD-001-LIQUID-V0.1
Primary predictor: cohort_divergence_pp.
Primary outcome: +4h simple_return_pct.
Secondary robustness outcome: +1h simple_return_pct.

Variation gate:
- at least 5 distinct predictor values overall;
- at least 3 distinct values per symbol.

If variation gate fails after readiness: INSUFFICIENT_FEATURE_VARIATION.

Frozen hypothesis: higher smart-money-minus-losing-crowd long divergence predicts higher subsequent signed return.

Primary analysis:
- within-symbol predictor ranks;
- pooled Spearman correlation with +4h simple return;
- source-only nearest-rank Q4 minus Q1 mean +4h simple return;
- leave-one-UTC-date-out sign checks.

SURVIVES_FORWARD requires:
- variation gate pass;
- primary Spearman rho > 0;
- Q4 minus Q1 > 0;
- at least 75% of leave-one-date-out folds preserve each positive sign;
- +1h Spearman sign non-negative;
- no single UTC date contributes more than 40% of total Q4-Q1 numerator magnitude.

Otherwise: NO_EDGE.

## Quartile firewall
Quartile cutpoints must be computed by a source-only script that reads observations but not outcomes. Numeric cutpoints are frozen in a separate source-only receipt before confirmatory outcome analysis.

## Terminal labels
FORWARD_INSUFFICIENT, INSUFFICIENT_FEATURE_VARIATION, SOURCE_BLOCKED, NO_EDGE, SURVIVES_FORWARD.

SURVIVES_FORWARD is research evidence only and does not authorize trading or capital deployment.
