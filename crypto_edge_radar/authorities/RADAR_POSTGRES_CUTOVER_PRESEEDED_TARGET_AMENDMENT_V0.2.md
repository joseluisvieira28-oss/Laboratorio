# CRYPTO EDGE RADAR — POSTGRES CUTOVER PRESEEDED TARGET AMENDMENT V0.2

Date: 2026-09-27
Status: **FROZEN BEFORE FINAL CUTOVER**
Parent authority: `RADAR_POSTGRES_CUTOVER_PROTOCOL_V0.1.md`

## Purpose

Permit the already-provisioned Supabase target to remain pre-seeded before final cutover without weakening any exact-evidence invariant.

This amendment does not authorize cutover by itself. It only replaces parent precondition 3 (empty target) with the exact-prefix rule below. Every other V0.1 requirement remains binding.

## Exact-prefix precondition

A non-empty target is acceptable only when all of the following are proven immediately before the quiesced reconciliation:

1. target event ids are a contiguous prefix beginning at id 1;
2. target event count is not greater than the final verified source snapshot;
3. every target event row is byte/text identical to the source row at the same id for id, event_ts, event_type, payload_json, payload_sha256, prev_chain_sha256 and chain_sha256;
4. every target event-key row is identical to the source binding;
5. target chain head equals the source chain hash at the target's last event id;
6. target contains no orphan, extra or conflicting event keys;
7. BIGSERIAL continuity is valid.

If any condition fails, classification is `PRESEEDED_TARGET_DIVERGENCE_FAIL_CLOSED` and cutover is forbidden.

## Final reconciliation

During V0.1 write quiescence:
- take and independently verify the final source snapshot;
- re-verify the pre-seeded target against that final snapshot;
- append only the exact missing source suffix, preserving original ids and payload_json text;
- append only the corresponding missing event-key bindings;
- never overwrite or rewrite an existing target event;
- verify full target equivalence to the final source snapshot;
- only after exact equivalence may DATABASE_URL be switched.

If target is already exactly equal to the final source snapshot, no row mutation is required.

## Target-ahead rule

If target contains any event id or event-key binding not present in the final verified source snapshot, do not delete it automatically and do not switch. Fail closed for manual forensic reconciliation.

## Secrets and safety

Connection credentials remain secret-only. No credentials may be committed, logged, inferred or printed.

No science changes. No outcome changes. No trading. No orders. No wallets. No exchange mutation. No capital. No automatic promotion. No main merge.
