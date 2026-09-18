# STETH-REDEMPTION-BASIS-002 — DISCOVERY IMPLEMENTATION BOUNDARY AMENDMENT V0.1A

Status: **FROZEN BEFORE DISCOVERY OUTCOMES**
Date: **2026-09-18**

This amendment corrects only the protected-period transport boundary in the implementation semantics freeze. It changes no economic rule.

Authority order:

1. PRE-SOURCE AUTHORITY V0.1
2. TIMESTAMP MAPPING TRANSPORT CLARIFICATION V0.1A
3. FINAL PRE-DISCOVERY PROTOCOL V0.1
4. DISCOVERY IMPLEMENTATION SEMANTICS FREEZE V0.1
5. this boundary amendment for the exact transport cap below.

## Exact cap

The canonical final snapshot is:

- timestamp target: 2024-12-31T12:00:00Z
- mapped block: **21,522,315**

For Discovery:

- block headers after 21,522,315 may be read **only if needed for timestamp-mapping verification**, under the already frozen header-only transport clarification;
- **no contract state call, economic value, event-log payload, queue finalization, TokenRebased data, Curve quote, PnL input or other economic source may be read after block 21,522,315**;
- no 2025/2026 data may be read under any circumstance.

Therefore a signaled position whose canonical finalization is not provable at or before block 21,522,315 is `PROTECTED_PERIOD_CENSORED`, unless its 14-day horizon already expired at or before that block without finalization, in which case it is `OPERATIONAL_HORIZON_FAILURE`.

A censored position blocks an edge PASS exactly as frozen in the implementation semantics.

Sections of the implementation freeze that referred to 2024-12-31T23:59:59Z as an economic-state/log limit are superseded by this stricter exact block cap.

No outcomes were opened before this amendment.
