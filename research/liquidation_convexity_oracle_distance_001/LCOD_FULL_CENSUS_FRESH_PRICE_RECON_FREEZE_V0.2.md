# LCOD FULL-CENSUS FRESH-PRICE RECONCILIATION V0.2 — FREEZE

Frozen: 2026-09-24
Outcomes: CLOSED

## Trigger

V0.1 four-group scale:
- census: 2,386 / 2,386 borrowers indexed;
- zero census/read errors;
- coverage: 89.6060%, just below frozen 90%;
- tolerance remained <=5e-5.

A frozen source-only remediation probe diagnosed PRICE_STALENESS_CONFIRMED:
23 / 24 preselected cached-price failures passed the unchanged tolerance when
reserve details were re-read immediately around the borrower component reads.
No dynamic collateral-factor difference was observed in that probe.

## V0.2 technical correction

The borrower/reconciliation logic, population, 4-group SHA split, debt identity,
HF formula, source endpoints, 90% coverage gate and <=5e-5 tolerance are unchanged.

Only this source-read behavior changes:
- V0.1 cached get_reserve_details across an entire group.
- V0.2 caches get_reserve_details only within one borrower evaluation.

No tolerance widening. No exclusion rescue. No market/liquidation outcome.

## PASS

Each of groups 0123 / 4567 / 89ab / cdef:
- >=90% eligible among debt-bearing indexed borrowers;
- zero census errors;
- zero silent component read errors.

Aggregate RECON pass requires all four groups PASS and union=current census.

## Critical boundary

Even if V0.2 passes, it does NOT establish one simultaneous protocol snapshot.
Sequential live reads occur over a nonzero capture interval.

Therefore:
FULL_CENSUS_FRESH_PRICE_RECON_PASS != CANONICAL_CURVE_SNAPSHOT_PASS

A separate block/time-consistency gate is mandatory before a protocol-wide
liquidation-convexity curve may receive scientific credit.
