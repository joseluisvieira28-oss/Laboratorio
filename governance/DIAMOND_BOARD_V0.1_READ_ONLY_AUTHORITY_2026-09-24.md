# CRYPTO LAB — DIAMOND BOARD V0.1 — READ-ONLY AUTHORITY — 2026-09-24

Status: FROZEN / OBSERVABILITY ONLY

Purpose: expose existing validation progress without changing scientific rules.

OPTIONS-SPOTPERP-001-V2.1 inherits its existing first-50 forward gate. Descriptive metrics before 50 never create an early verdict.

CED1D-0031 inherits the existing 60-event / 8-week / 50-execution-pair gate. AVAX20 cross-venue evidence from PR #32 is supporting evidence only, not independent time OOS.

ETF-CME-INSTFLOW-001 inherits the earlier Q4 V0.1A no-peek authority. Only source/timing status may be shown before the one-shot final evaluation after 2027-01-01T00:00:00Z. Interim PnL/PF/outcomes are forbidden.

BNB-LAUNCHPOOL-DEMAND-001 may show canonical watcher status. Diamond V0.2 remains draft under PR #88 and is not canonical authority.

The board reads already-constructed runtime state only. It performs no market-source fetch, no new strategy calculation, no evidence write, no order, no exchange mutation, no capital action and no automatic promotion.

The read-only `/api/diamond` endpoint returns the same governance view embedded in `/api/state`.

No scientific threshold change. No live-trading authority. No authenticated trading API. No wallet. No leverage change. No main merge implied.
