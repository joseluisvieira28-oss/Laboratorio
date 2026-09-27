# CBETH-REDEMPTION-BASIS-001 — MECHANISM DISCOVERY STATISTICAL GATE FREEZE V0.1B

Frozen: 2026-09-27
Parents:
- PRE_OUTCOME_PREDICTOR_DESIGN_FREEZE_V0.1
- MECHANISM_SAMPLE_BOUNDARY_ADDENDUM_V0.1A

Timing:
BEFORE source-gate execution, dense predictor values, q10/q90 values, event counts or mechanism outcomes.

## Preconditions

Mechanism Discovery may be computed only when:
- SOURCE_PASS;
- complete predictor census PASS;
- calibration PASS;
- PREDICTOR_SAMPLE_PASS;
- MECHANISM_SAMPLE_PASS after the frozen 12-day calendar boundary.

Otherwise no mechanism statistic is opened.

## Primary event metric

For each eligible event:

signed_closure_12d =
- DISCOUNT_EXTREME: basis_(t+12d) - basis_t
- PREMIUM_EXTREME: basis_t - basis_(t+12d)

Positive means movement toward the protocol conversion anchor.

## Frozen aggregate statistics

Compute:
1. pooled arithmetic mean signed_closure_12d;
2. DISCOUNT_EXTREME arithmetic mean;
3. PREMIUM_EXTREME arithmetic mean;
4. deterministic nonparametric event-row bootstrap of pooled mean:
   - 10,000 resamples;
   - sample size = original eligible event count;
   - with replacement;
   - PRNG seed = 20260927;
   - percentile 95% confidence interval.

## Discovery PASS

MECHANISM_DISCOVERY_PASS requires ALL:
- pooled mean signed_closure_12d > 0;
- bootstrap 95% lower bound > 0;
- discount-tail mean signed_closure_12d > 0;
- premium-tail mean signed_closure_12d > 0.

Otherwise:
MECHANISM_DISCOVERY_FAIL.

No p-value or secondary metric may replace these criteria.

## Secondary diagnostic

3-calendar-day signed closure may be reported descriptively for eligible events whose exact future daily observation exists.

It:
- has no PASS criterion;
- cannot rescue the primary;
- cannot redefine the primary horizon.

## After Discovery

MECHANISM_DISCOVERY_FAIL:
close exact LAB_ID; OOS 2025 remains CLOSED.

MECHANISM_DISCOVERY_PASS:
zero trading-edge promotion by itself; a separate pre-frozen OOS-opening authority is required before any 2025 OOS outcome is read.

2026 remains protected regardless of Discovery result.

## No PnL

This test is protocol-basis convergence only.
No fees, slippage, trade construction, leverage, PnL, execution route or live order is authorized.
