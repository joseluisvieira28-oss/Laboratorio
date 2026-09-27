# CRYPTO EDGE RADAR — DATABASE TARGET MODE TELEMETRY V0.1 — 2026-09-27

Status: **FROZEN OPERATIONAL TELEMETRY / NO SCIENCE CHANGE**

Authority ID: `RADAR-DATABASE-TARGET-MODE-TELEMETRY-V0.1`

## Purpose

Make the active canonical evidence-store target explicitly observable after the future Supabase cutover.

Both the expiring Render source and the prepared Supabase target are PostgreSQL, so the existing public state field:

`evidence_backend = postgres`

cannot distinguish which database is actually active.

## Allowed telemetry

Expose exactly one additional non-secret state field:

`database_target_mode`

Allowed values are inherited from existing Settings:
- `SOURCE`
- `SUPABASE_POOLER`

The field may appear in:
- STARTING state;
- normal runtime heartbeat;
- fail-closed runtime state;
- write-quiesced maintenance state.

## Forbidden content

This telemetry must never expose:
- DATABASE_URL;
- Supabase pooler hostname;
- database username;
- database password;
- connection string;
- source connection URL;
- provider token.

## Semantics

`SOURCE` means the runtime selected the existing source database path.

`SUPABASE_POOLER` means the runtime selected the frozen Supabase Shared Session Pooler target path through the explicit `RADAR_USE_SUPABASE_TARGET=true` switch.

The field is descriptive only. It does not authorize switching, cutover, migration, trading, orders or capital.

## Firewalls

- science_changed=false
- outcomes_changed=false
- evidence_rows_changed=false
- source_mutation=false
- target_mutation=false
- orders=false
- exchange_mutation=false
- live_capital=false
- automatic_cutover=false
- secret_value_exposed=false
- main_merge=false
