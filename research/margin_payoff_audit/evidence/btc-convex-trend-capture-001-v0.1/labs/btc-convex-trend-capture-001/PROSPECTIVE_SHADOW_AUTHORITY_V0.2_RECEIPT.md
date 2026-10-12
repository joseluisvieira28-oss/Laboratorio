# BTC-CONVEX-TREND-CAPTURE-001 — V0.2 AGGRESSIVE FORWARD AUTHORITY RECEIPT

**Authority file:** PROSPECTIVE_SHADOW_AUTHORITY_V0.2_AGGRESSIVE.md  
**Freeze commit:** 673d50b2f786e88c593a900db1a9aac6a265d215  
**Freeze commit timestamp:** 2026-09-24T06:17:04Z

## Resolved boundary

Authority rule:
first eligible V0.2 1h bar OPEN must be strictly later than the freeze commit timestamp.

Therefore:

- first eligible bar open: **2026-09-24T07:00:00Z**
- first eligible bar close boundary: **2026-09-24T08:00:00Z**
- no signal, fill, funding observation or trade before 07:00:00Z receives V0.2 credit
- the first 07:00 bar becomes causally observable only after it has fully closed at 08:00:00Z

## Checkpoints

- A: >=10 V0.2 resolved family trades
- B: >=25 trades AND >=2 symbols with >=5 closed trades
- C: >=50 trades AND >=3/4 symbols with >=5 closed trades AND clean source/causal integrity

No calendar-day minimum.

Checkpoint C triggers V3 re-adjudication; it does not auto-promote.

## Status at freeze

**TIER 3 — WATCHLIST / FORWARD-ONLY**  
**LIVE CAPITAL: NOT AUTHORIZED**
