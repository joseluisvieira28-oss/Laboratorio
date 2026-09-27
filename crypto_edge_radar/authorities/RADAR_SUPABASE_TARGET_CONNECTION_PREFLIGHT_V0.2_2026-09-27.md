# CRYPTO EDGE RADAR — SUPABASE TARGET CONNECTION PREFLIGHT V0.2 — 2026-09-27

Status: **FROZEN READ-ONLY PREFIX-AWARE PRE-CUTOVER PREFLIGHT**

Authority ID: `RADAR-SUPABASE-TARGET-PREFLIGHT-V0.2`

Parent authorities:
- `RADAR_POSTGRES_CUTOVER_PROTOCOL_V0.1`
- `RADAR_POSTGRES_CUTOVER_PRESEEDED_TARGET_AMENDMENT_V0.2`
- `RADAR_POSTGRES_APPEND_ONLY_PREFIX_RECONCILIATION_V0.1`

## Frozen backup identity

The verified backup boundary remains immutable:
- events: 1032
- keys: 954
- max event id: 1032
- chain head: `f8b85ba3d45dcb426e37d1a1da543cff61a85d9ea0a01ddc1a07662b9e7c02cd`
- canonical snapshot SHA256: `6c74bdcf1013b1ab49fdcefd2e046db6471ea2816c6b425f4a6378dda22de9cb`

This V0.2 does not replace or rewrite that boundary.

## Why V0.2 exists

The Supabase target is append-only and may legitimately contain events after the frozen 1032-event backup boundary before the final cutover.

Therefore a credential preflight must not require the entire current target to remain exactly 1032 rows. It must instead prove:
1. the complete current target evidence chain verifies;
2. current event ids are contiguous from 1;
3. the target sequence equals the current max event id;
4. the exact first 1032 events remain the frozen backup prefix;
5. all event-key bindings whose event_id is <=1032 remain exactly the frozen 954-key set;
6. the boundary chain head and canonical snapshot hash remain exactly frozen;
7. any current suffix is descriptive only and does not authorize cutover.

## Pass classification

`TARGET_PREFLIGHT_PASS_BACKUP_PREFIX_CURRENT_CHAIN_OK`

This classification proves only:
- the supplied secret reaches the intended target;
- the target's frozen backup prefix is intact;
- the complete current target chain is internally valid.

It does **not** prove final source/target equality.

## Final cutover remains blocked until

1. source writes are quiesced;
2. final source snapshot is taken and independently verified;
3. target exact-prefix reconciliation is run against that final snapshot;
4. any missing exact suffix is appended under the frozen reconciliation authority;
5. sequence is finalized if required;
6. full target equivalence is independently verified;
7. only then may DATABASE_URL / target switch be authorized.

## Secret handling

Input remains:
`RADAR_MIGRATION_TARGET_URL`

The URL/password must never be logged, hashed, persisted, committed or surfaced in state.

## Firewalls

- read-only transaction only;
- no INSERT / UPDATE / DELETE;
- no DDL;
- no sequence mutation;
- no source mutation;
- no science or outcome changes;
- no orders;
- no exchange mutation;
- no live capital;
- no automatic cutover;
- no main merge.
