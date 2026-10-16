# LICP-HIST-XALT-003 — HOLDOUT INTEGRITY AUDIT V0.1

Date: 2026-09-26
Status: PROCEDURAL DEVIATION RECORDED

## Canonical holdout opening
Canonical first outcome run:
- workflow run: 36234052123
- head commit: 8b79401ee4114d3b097b3664d5ef738e2b3832cc
- decision: HOLDOUT_SURVIVES

Frozen candidate at first opening:
- target: SOLUSDT
- direction: SHORT
- entry proxy: t0 + 6m
- horizon: 60m
- transfer hurdle: 16 bps

## Unintended duplicate opening
A second workflow run recalculated the same locked holdout:
- workflow run: 36234349727
- head commit: 1949be52dc378416e89f93fff12ddfd02d2de05e
- decision: HOLDOUT_SURVIVES
- numerical result: identical to canonical first run

Cause:
A later workflow-only commit retriggered the holdout workflow.

## No-tuning verification
The scientific holdout code and selected-candidate freeze were byte-identical across the two runs.

Holdout script blob SHA in BOTH runs:
- db646d72737efba4baf35c54d2c9b4c7e375b68c

Selected-candidate holdout freeze blob SHA in BOTH runs:
- d491db7677406377fc63cfb9d6651b448b18d3bb

Therefore:
- no threshold changed;
- no target changed;
- no horizon changed;
- no direction changed;
- no entry delay changed;
- no outcome-dependent rescue occurred;
- the duplicate run did not change candidate selection or scientific code.

## Governance decision
The literal "open exactly once" procedure was violated.

The first run remains the canonical holdout result, but the result must NOT be described as a pristine single-pass holdout without this caveat.

State:
HOLDOUT_SURVIVES_WITH_EXECUTION_DEVIATION

This does not invalidate the identical first-run outcome, but it reduces procedural purity and raises the importance of the independent forward MEXC transfer study.

## Prevention
A repository lock is added after this audit.
Any future XALT-003 holdout workflow execution must fail closed before reading outcome data.

No further XALT-003 holdout rerun is scientifically authorized.
