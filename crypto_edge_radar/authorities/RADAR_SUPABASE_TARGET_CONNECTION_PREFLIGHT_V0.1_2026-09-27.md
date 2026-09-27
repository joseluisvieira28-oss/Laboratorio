# CRYPTO EDGE RADAR — SUPABASE TARGET CONNECTION PREFLIGHT V0.1 — 2026-09-27

Status: **FROZEN READ-ONLY PRE-CUTOVER PREFLIGHT**

Authority ID: `RADAR-SUPABASE-TARGET-PREFLIGHT-V0.1`

Parent authorities:
- `RADAR_POSTGRES_CUTOVER_PROTOCOL_V0.1`
- `RADAR_POSTGRES_PORTABILITY_V0.1`

Verified target equivalence boundary:
- target provider: Supabase
- project ref: `jqzdvgjeuveiktftyrlz`
- project name: `crypto-edge-radar-evidence-v05`
- events: 1032
- keys: 954
- max event id: 1032
- chain head: `f8b85ba3d45dcb426e37d1a1da543cff61a85d9ea0a01ddc1a07662b9e7c02cd`
- event rowset SHA256: `f1fdde4843b8c33f42a2a90896ef4d86df411d02c00e25d551576b53f7a8efa2`
- event-key rowset SHA256: `978f6eea3070fbadd73ccb4688028a9f3dcf07ab5876ccdc47cfa53c2debf02d`

## Purpose

Validate a legitimate target PostgreSQL connection URL before any maintenance/quiescence window and before any DATABASE_URL switch.

## Secret handling

The target URL is accepted only from:
`RADAR_MIGRATION_TARGET_URL`

The tool must never print, hash, persist or commit the URL or password.

No URL configured => `AUTH_REQUIRED_NOT_EXECUTED`.

## Frozen preflight

The preflight may perform only:
- TLS/Postgres connection;
- `SET TRANSACTION READ ONLY`;
- identity/engine metadata reads;
- row counts;
- min/max/distinct event-id reads;
- chain-head read;
- BIGSERIAL sequence read;
- deterministic server-side rowset digest reads;
- orphan-key count;
- schema/table existence checks.

It must not:
- create/alter/drop any object;
- insert/update/delete rows;
- set sequences;
- quiesce the source;
- switch DATABASE_URL;
- change science/outcomes;
- create orders/exchange mutation/capital.

## Acceptance

At the frozen 1032-event boundary, `TARGET_PREFLIGHT_PASS_AT_BACKUP_BOUNDARY` requires exact equality with the frozen target-equivalence receipt.

If the source has advanced beyond 1032 events, that does NOT invalidate this preflight; it only proves that this credential reaches the already-verified target. Final cutover still requires a new quiesced source snapshot and exact target reconciliation.

Any mismatch => fail closed.

## Governance

database_mutation=false
source_mutation=false
science_changed=false
outcomes_changed=false
orders=false
exchange_mutation=false
live_capital=false
automatic_cutover=false
main_merge=false
