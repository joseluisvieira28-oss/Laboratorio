# ETF-CME-INSTFLOW-001 — PREARM TRANSPORT HARDENING V0.3 — 2026-09-24

**Status:** FROZEN BEFORE ANY NEW POST-2026-09-24 EXACT-TIME OBSERVATION
**Scope:** technical/runtime only
**Scientific rule changes:** NONE
**Q4 outcome authority:** `ETF-CME-INSTFLOW-001-FORWARD-SHADOW-Q4-2026-V0.1A` remains fully controlling.

## Problem observed

The exact scheduler can encounter transient CFTC HTTP failures while discovering the latest public CFTC observation. The runtime state also retained a stale `error` field after a later successful discovery because state updates were merged.

At the exact target, the previous implementation performed another CFTC source fetch even after it had already fetched and prearmed the exact same source observation inside the frozen 60-second arm window. A transient failure on that duplicate transport call could convert an otherwise valid exact observation into a technical miss.

This is an operational transport defect, not a scientific failure and not permission to widen the timing window.

## Frozen remediation

1. A CFTC public snapshot fetched inside the existing 60-second arm window may be held **in process only** for the exact target.
2. The snapshot contains exactly the same prior/current CFTC observations used to compute the existing frozen signal.
3. At the exact target, the watcher may persist from that prearmed snapshot instead of performing a second source fetch.
4. Snapshot age must be <= `arm_lead_seconds + max_late_seconds` (currently 60 + 2 seconds).
5. Snapshot current as-of date must remain strictly after the old runtime boundary (`2026-09-15`).
6. If the prearmed snapshot is absent, stale, mismatched or outside the frozen arm window, fail closed.
7. No late chase is introduced.
8. The exact target and +2 second technical lateness budget are unchanged.
9. A transient source failure near a previously known exact target retries the source loop at the existing 0.25-second final wait slice only while inside the frozen arm/expiry window.
10. Successful state transitions clear stale transport error text; historical error receipts remain preserved in logs/evidence.

## Q4 no-peek firewall

This remediation does **not** access BTC outcomes.

The earlier Q4 V0.1A authority still requires:
- source-only CFTC checkpointing during Q4;
- no BTC forward-outcome price fetch before 2027-01-01T00:00:00Z;
- exactly one final economic evaluation;
- no interim PnL, PF, drawdown or partial-sample verdict.

## Historical miss

The 2026-09-23 exact observation remains:
`MISSED_EXPECTED_OBSERVATION_NO_CHASE`.

This patch must never reconstruct it.

## Governance

- public/read-only source only;
- no authenticated trading API;
- no order;
- no exchange mutation;
- no capital;
- no wallet;
- no leverage change;
- no signal/direction/horizon/cost change;
- no main merge implied.
