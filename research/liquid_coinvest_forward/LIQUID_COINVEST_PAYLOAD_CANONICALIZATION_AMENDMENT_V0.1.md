# LIQUID CO-INVEST FORWARD — PAYLOAD CANONICALIZATION AMENDMENT V0.1

Date: 2026-10-05
Branch: liquid-coinvest-forward-v0.1-prereg-2026-10-05
Status: ACTIVE / TECHNICAL-ONLY / FROZEN BEFORE ANY SUCCESSFUL OUTCOME RECEIPT

## Triggering incident

Workflow run 37310929996 stopped before outcome access because ETH repeated the same source_created_at_utc while floating-point JSON serialization differed at sub-micro-dollar precision (for example 34968210.96979 versus 34968210.969790004).

The economic/source payload was unchanged for scientific purposes. Treating Python/JSON float rendering noise as a proprietary source advance or SOURCE_INTEGRITY_CONFLICT is a serialization bug.

## Frozen semantic comparison

Observation receipts remain immutable.

For source-event classification only:
- position_count is compared exactly as an integer;
- tier identity (min/max/size) is compared exactly after existing string normalization;
- monetary fields total_position_value, total_position_value_long and value_close_to_liquidation are equal when math.isclose(rel_tol=1e-12, abs_tol=1e-6);
- bias is equal when math.isclose(rel_tol=1e-12, abs_tol=1e-12).

If all fields are semantically equal under these tolerances and source_created_at_utc is unchanged, classify DUPLICATE_SOURCE_SNAPSHOT.

If source_created_at_utc advances and the semantically compared payload advances, classify EVENT_ELIGIBLE.

If source_created_at_utc advances but the semantically compared payload does not, classify SOURCE_TIMESTAMP_ONLY.

If source_created_at_utc is unchanged but any scientifically material field changes beyond these tolerances, classify SOURCE_INTEGRITY_CONFLICT and fail closed.

This amendment changes serialization equivalence only. It does not change venue, source, predictor definitions, horizons, outcomes, event direction, sample gate, or confirmatory decision rules.
