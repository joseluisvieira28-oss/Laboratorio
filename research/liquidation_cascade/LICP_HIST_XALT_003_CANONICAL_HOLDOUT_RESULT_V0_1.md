# LICP-HIST-XALT-003 — CANONICAL HOLDOUT RESULT V0.1

Date: 2026-09-26
Status: HOLDOUT_SURVIVOR / HISTORICAL COARSE EVIDENCE

## Canonical run
The ONLY scientific holdout opening is GitHub Actions run 36234052123.

Pre-outcome chronology:
- selected-candidate freeze commit 350e3a36c6f709db2a8ca8baf620af86417260ab at 2026-09-26T09:51:45Z
- holdout runner commit 7c1947e44e965f6b9aceff7218aa90870059b4e4 at 2026-09-26T09:51:47Z
- workflow commit 8b79401ee4114d3b097b3664d5ef738e2b3832cc at 2026-09-26T09:51:49Z
- canonical holdout run created after the above freeze/runner/workflow commits

A later workflow rerun (36234349727) reproduced the same values exactly. It is NON-CANONICAL and contributes zero additional statistical evidence.

## Frozen candidate
- BTC liquidation ignition
- SOLUSDT SHORT continuation
- entry proxy t0 + 6 minutes
- horizon 60 minutes
- transfer hurdle 16 bps
- locked partition 2025-11-01 through 2025-12-31

## Canonical holdout outcome
Eligible BTC ignition events: 35
Valid: 35
Missing: 0
Missing rate: 0%

Pooled:
- mean gross = +25.071392225575067 bps
- median gross = +16.8823860438937 bps
- positive rate = 60%
- mean transfer-ceiling net after 16 bps hurdle = +9.071392225575067 bps

November 2025:
- n = 15
- mean gross = +2.707481425552385 bps
- median gross = +23.91441157960953 bps
- positive rate = 53.33%

December 2025:
- n = 20
- mean gross = +41.844325325592074 bps
- median gross = +14.384981762712773 bps
- positive rate = 65%

## Frozen verdict
HOLDOUT_SURVIVES.

All predeclared holdout gates passed:
- n >= 20: PASS
- pooled mean gross > 16 bps: PASS
- pooled median gross > 0: PASS
- November mean gross > 0: PASS
- December mean gross > 0: PASS
- missing-price rate <= 10%: PASS

## Interpretation boundary
This is a legitimate historical holdout survivor for the frozen coarse BTC-ignition -> SOL second-wave hypothesis.

It is NOT executable PnL.
It does NOT prove MEXC transferability.
It does NOT prove a real-time sensor equivalent to the historical event source.
It creates NO live-trading authority.

LICP-HIST-XALT-003 V0.1 is CLOSED to tuning. No reranking, rescue, alternate horizon, alternate target, alternate delay, or repeat holdout may change this verdict.

Next legitimate gate: LICP-FWD-XALT-004 forward transfer, only after its frozen live trigger dependency is satisfied.
