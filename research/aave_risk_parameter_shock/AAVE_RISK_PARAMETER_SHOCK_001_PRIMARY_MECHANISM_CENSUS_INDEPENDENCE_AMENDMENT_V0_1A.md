# AAVE-RISK-PARAMETER-SHOCK-001 — PRIMARY MECHANISM CENSUS INDEPENDENCE AMENDMENT V0.1A

Date: 2026-09-18
Status: FROZEN BEFORE ANY liquidationThreshold VALUE DECODING

## Reason

Transaction-level clustering alone can overstate independence when one governance execution changes multiple risk parameters across more than one transaction in a short interval.

## Amendment

The raw same-transaction cluster remains an auditable structural grouping, but the minimum sample gate is adjudicated on independent shock episodes.

Sort threshold-decrease transaction clusters chronologically by their earliest timestamp.
Start an episode at the first cluster.
Any later threshold-decrease cluster whose earliest timestamp is <= 24 hours after the episode start belongs to the same episode.
The first later cluster >24 hours after the episode start begins a new episode.

This is fixed-window episode clustering, not rolling single-linkage.

## Revised minimum gate

MECHANISM_CENSUS_PASS requires:
- at least 12 independent 24-hour threshold-decrease episodes;
- at least 4 unique affected collateral assets;
- qualifying episodes in at least 2 UTC calendar years;
- all provenance and duplicate checks PASS.

The older transaction-cluster count remains reported but is not the independence gate.

No threshold magnitude filter, asset selection, event-family substitution or outcome access is authorized.
