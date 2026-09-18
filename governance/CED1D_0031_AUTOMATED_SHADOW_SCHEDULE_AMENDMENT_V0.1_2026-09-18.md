# CED1D-0031 — AUTOMATED SHADOW SCHEDULE AMENDMENT V0.1 — 2026-09-18

**Status:** FROZEN BEFORE FIRST SCHEDULED REAL PROSPECTIVE SHADOW COLLECTION  
**Candidate:** CED1D-0031 — AVAXUSDT Momentum 20D CONTINUATION H1

This amendment changes operational scheduling only. It does not change the frozen collector V0.2A, signal, lookback, direction, horizon, funding, execution proxy, costs, notional, evidence gates, or prospective boundary.

## Automated cadence
- GitHub Actions scheduled once per UTC day.
- For scheduled runs, `through_signal_day = UTC today - 3 calendar days`.
- The existing collector `SOURCE_READINESS_GUARD` remains authoritative and fail-closed.
- Before 2026-09-21 UTC the scheduled path must exit without collecting a forward outcome because no eligible T+3 signal day exists.
- Manual `workflow_dispatch` remains available and must obey the same guard.

## Governance
- public/read-only data only
- no account API keys
- no authenticated trading endpoints
- no orders
- no exchange mutation
- no wallets
- no leverage
- no production capital
- no retrospective pre-boundary outcome backfill
- no auto-promotion
- no merge to main
