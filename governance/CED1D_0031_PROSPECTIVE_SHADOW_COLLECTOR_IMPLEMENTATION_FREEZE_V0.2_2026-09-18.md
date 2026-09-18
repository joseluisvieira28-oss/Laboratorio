# CED1D-0031 — PROSPECTIVE SHADOW COLLECTOR IMPLEMENTATION FREEZE V0.2 — 2026-09-18

**Status:** FROZEN BEFORE ANY REAL PROSPECTIVE SHADOW MARKET OUTCOME  
**Candidate:** CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1  
**Branch:** `ced-1d-v3-byte-recovery-2026-09-17`

## Purpose

V0.2 prospectively fixes only the pre-boundary lookback-source acquisition semantics of collector V0.1.

The frozen strategy itself is unchanged:
- symbol: AVAXUSDT
- family: A_MOMENTUM
- lookback: 20 valid completed daily observations
- direction: CONTINUATION
- horizon: 1 calendar day
- reference entry/exit: exact 00:01 UTC open
- reference BASE/STRESS nonfunding costs: 14 / 20 bps
- execution research notional: 100 USDT/leg
- aggTrades, bookDepth, funding and markPrice rules: unchanged
- operational checkpoint: 10 resolved events + 14 calendar days
- Tier-1 evidence minimum: 60 completed prospective events + 8 complete UTC signal weeks

## Correction

V0.1 initialized warm-up with exactly 20 calendar days before the first eligible signal day.

The inherited V0.3 CED implementation does NOT define Momentum over 20 calendar days. It defines it over 20 prior **valid daily observations**.

Therefore a single invalid/missing pre-boundary day could make V0.1 under-acquire lookback input and incorrectly return no signal rather than continue backward to the 20th prior valid day.

No real shadow collector run occurred under V0.1.
No prospective market outcome was opened under V0.1.
The issue was found by static audit before the first eligible signal completion.

V0.2 changes only source acquisition:
- walk backward from 2026-09-17;
- fetch one prior daily source at a time;
- count only valid 1,440-minute, zero-duplicate days;
- stop when exactly 20 prior valid daily observations are available;
- maximum search guard: 120 calendar days;
- if 20 valid days cannot be recovered inside that guard: FAIL CLOSED;
- all pre-boundary rows are LOOKBACK_INPUT_ONLY and cannot enter performance evidence.

This is an implementation-correctness amendment, not a signal or parameter change.

## Frozen identities

Collector:
- path: `Dream-Account-OS-v2.3-PARTIAL/research/ced_1d_v3/ced1d_0031_prospective_shadow_collector_v02.py`
- Git blob: `5d4f53995060b5127ad44f0b825bff8ddf3fea7f`

Synthetic QA:
- path: `Dream-Account-OS-v2.3-PARTIAL/research/ced_1d_v3/tests/test_ced1d_0031_prospective_shadow_collector_v02.py`
- Git blob: `d3c4e2525e4e0023e3fa40f0733b65b3b998245e`

QA workflow:
- path: `.github/workflows/ced1d-0031-prospective-shadow-synthetic-qa-v02.yml`
- Git blob: `fd1c48cf9971a1ac2dca14bf92f561d03aa2822d`

Controlling activation authority:
- path: `governance/CED1D_0031_TIER2_SHADOW_ACTIVATION_AUTHORITY_V0.2_2026-09-18.json`
- Git blob: `f524aebd3cbae48b6dd916b1fba87aa88d94d2f4`

Synthetic QA run:
- run: `35351865506`
- conclusion: SUCCESS
- real prospective source access: FALSE
- real 2026 shadow outcome opened: FALSE

## V0.1 precedence

Collector V0.1 and its implementation freeze remain preserved for audit history.

For any first real prospective shadow collection after this freeze:
**V0.2 supersedes V0.1 operationally.**

V0.1 MUST NOT be dispatched for real shadow evidence.

## Prospective boundary unchanged

First eligible signal day:
`2026-09-18`

First eligible signal completion:
`2026-09-19T00:00:00Z`

First eligible reference entry:
`2026-09-19T00:01:00Z`

No pre-boundary signal outcome may be admitted.

## Firewall

Still forbidden:
- live trading
- real orders
- authenticated exchange trading endpoints
- account keys
- balances/positions
- wallets
- leverage
- exchange mutation
- execution webhooks
- parameter tuning
- retrospective 2026 performance backfill
- merge to main

The collector remains public/read-only research only.
