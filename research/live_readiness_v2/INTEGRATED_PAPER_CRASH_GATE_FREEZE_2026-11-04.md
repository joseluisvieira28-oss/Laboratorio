# Live Readiness V2 — Integrated Paper Executor, crash boundary pre-test freeze
Date 2026-11-04 UTC, isolated PR #334 research branch. **NO_LIVE_GO; no exchange or authenticated API.**

## Problem
Previously independently tested `risk_firewall.py` has 69/69 offline mock tests; `single_writer_recovery.py` has 48/48 Linux and Windows single-writer/restart tests. Neither proves the **gap across a durable local reservation and an independently accepted exchange-side order**. A crash between two writes must never create an automatic duplicate, hidden exposure or reset of a loss lock. This integration only establishes simulation behavior, not production exactly-once broker semantics.

## Frozen integration design before new test outputs
1. Use the existing `Policy`, `Quote`, `Account`, `Intent`, `Firewall._preflight` unchanged as the **pure paper risk preflight**. The existing risk journal and `PAPER_ARMED` status remain a temporary in-process gate, never exchange authorisation.
2. Single authoritative local `PaperFencedStore` with SQLite WAL / BEGIN IMMEDIATE and epoch/PID-scoped ticket reserves a unique `client_id` **before** any paper broker side effect.
3. Separate mock-broker SQLite file has independently durable simulated accepted orders/stops. No network, API SDK, order endpoints, keys or live path.
4. Deliberately introduce failures (a) after local reservation but before broker acceptance, (b) after broker accepts but before local fill receipt, (c) after broker stop acknowledges but before local protected receipt. Recovery MUST default frozen and must compare independent mock-broker open positions, orders, stops and local pending rows. Never blind retry same client ID or automatically clear exposed uncertainty.
5. A flat broker snapshot may permit paper-only recovery with explicit boolean test human approval **only when zero open positions and zero unresolved orders/stops**. This is a mock fixture, not an authenticated human/broker proof.
6. Loss-stop must be durable through restart and must not reset on mock human reconciliation. If integration cannot establish this atomically, report `INTEGRATION_RISK_LOCK_BLOCKED`; do not invent a PASS.
7. One active physical paper instrument BTC_USDT; no multiple simultaneous physical positions, no leveraging capital, no user account queries. Idempotency persists across epochs.
8. Test Linux and Windows CI with rigorous pipefail and original independent audit log artifact. Use child processes and hard `os._exit` for actual interruption; no claims of physical power-loss durability.
9. **No strategy/fee/stop-horizon updates** to PR #333, #107, #200, #223, #226 or protected holdouts. No `main` merge.

## Decisive outcome
`PAPER_INTEGRATION_FAULT_INJECTION_PASS_LIMITED` only if separate mock exchange and local custody agree after forced failures, duplicate/new entry risk is blocked, loss stops persist, test logs genuinely pass on Windows and Linux, and test source has zero live transport.
Otherwise `PAPER_INTEGRATION_BLOCKED`.
**Both are distinct from `LIVE_GO` and from profitable economic edge.**
