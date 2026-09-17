# CRYPTO EDGE RADAR V0.5 — POSTGRES CANARY PASS

Date: 2026-09-17
Branch: `crypto-edge-radar-postgres-v0.5`
Render service: `crypto-edge-radar-v05-canary`
Render region: Frankfurt
Mode: `PUBLIC_SHADOW_ONLY`

## Verdict

`POSTGRES_PERSISTENCE_CANARY_PASS`

The Render V0.5 canary successfully started with the configured remote Postgres evidence backend and produced three consecutive healthy runtime heartbeats on the same instance.

## Runtime evidence

Instance: `srv-dalqkpu1egvs73fhiehg-5d2b7`

1. Cycle 1 — `evidence_backend=postgres`, `health=OK`, `consecutive_failures=0`, `evidence_event_id=3`, `evidence_chain_sha256=95ca9ebe2a64e960d399665b359ea82738c15b12064bd7270c44aad98f2ce8ca`, `registered_strategies=0`, `valid_signal_count=0`.
2. Cycle 2 — `evidence_backend=postgres`, `health=OK`, `consecutive_failures=0`, `evidence_event_id=6`, `evidence_chain_sha256=24bd03d398840241180291395da5028ddecb1dd02869c244852a65e4fa071f60`, `registered_strategies=0`, `valid_signal_count=0`.
3. Cycle 3 — `evidence_backend=postgres`, `health=OK`, `consecutive_failures=0`, `evidence_event_id=9`, `evidence_chain_sha256=2f456ee64c5f37ce2f6f79822d9244ca2fbe273681ca6d94cf33f9e07ffe79d7`, `registered_strategies=0`, `valid_signal_count=0`.

## Safety invariants preserved

- No live orders.
- No authenticated exchange account/order paths.
- Runtime remains `PUBLIC_SHADOW_ONLY`.
- Empty strategy registry remains empty; no signals are invented.
- Evidence writes are remote Postgres and chain-hashed.
- Postgres backend is fail-closed when configured but unavailable.

## Scope limit

This proves the Postgres persistence canary gate. It does **not** promote any trading strategy, authorize live execution, or establish long-term production durability beyond the current Render/Postgres plan limits.

Next gate: controlled soak / durability observation before any production designation.
