# LCOD-001 SCHEDULER RESILIENCY ADDENDUM V0.1

Date frozen: 2026-09-26
Parent authority: LCOD_PROSPECTIVE_MECHANICAL_STATE_OBSERVATION_FREEZE_V0.1
Scope: scheduling/orchestration only. No scientific predictor, source, curve, threshold, outcome or trading rule changes.

## Problem

The dedicated default-branch LCOD scheduler did not emit the expected 2026-09-26 03:17 UTC run.
The LCOD scientific workflow itself remains valid; FORWARD_OBSERVATION_001 is already persisted and indexed.

## Canonical daily target

Primary target remains 03:17 UTC daily.

## Recovery heartbeat

A previously existing, independently scheduled default-branch workflow that demonstrably emits schedule events may act as a recovery heartbeat.

A recovery invocation may be classified as canonical only when ALL conditions hold:

1. caller event is GitHub `schedule`;
2. current UTC time is at or after 03:17 and before 12:00 UTC;
3. the LCOD forward series index contains no canonical observation whose `captured_at_utc` UTC calendar date equals the current UTC date;
4. the called LCOD workflow receives `canonical_trigger=true`;
5. the scientific workflow uses one finalized Ethereum block N/H resolved exactly once for that observation;
6. all frozen population/component/curve gates pass unchanged.

The first qualifying scheduled recovery heartbeat of a UTC day is eligible.
After a canonical observation exists for that UTC day, all later heartbeats must skip LCOD.

## Non-canonical invocations

The following never add to the scientific sample:
- workflow_dispatch / manual invocations;
- push-triggered runs;
- calls before 03:17 UTC;
- calls at or after 12:00 UTC;
- duplicate same-day runs;
- retrospective runs for a missed prior UTC date.

## Missed days

A day with no qualifying successful scheduled observation remains missed.
It is not backfilled and does not count toward either the 30-observation or 21-distinct-day gate.

## Scientific boundary

This addendum changes only transport/orchestration reliability.
It does not open:
- market returns;
- future liquidation outcomes;
- PnL;
- trading;
- exchange or wallet mutation.

It does not alter:
- the 13-Spoke universe;
- finalized-block semantics;
- active-debt definition;
- HF tolerance;
- coverage gates;
- frozen nine-point shock grid;
- predictor transformation;
- promotion criteria.

Recovery timing is durably recorded through each snapshot's captured timestamp and workflow provenance.
