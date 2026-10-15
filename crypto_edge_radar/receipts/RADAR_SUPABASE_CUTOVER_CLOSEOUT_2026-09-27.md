# CRYPTO EDGE RADAR — POSTGRES → SUPABASE CUTOVER CLOSEOUT — 2026-09-27

Status: **CUTOVER COMPLETE / SUPABASE CANONICAL / POST-CUTOVER RESTART + IDEMPOTENCY PASS**

Classification: `RADAR_SUPABASE_CUTOVER_COMPLETE__CHAIN_CONTINUITY_AND_RESTART_RECOVERY_PASS`

## Scope and authority

Operational persistence hardening only.

- science_changed = false
- outcomes_changed = false
- trading_rules_changed = false
- authenticated_exchange_api_used = false
- orders_created = false
- exchange_mutation_performed = false
- live_capital_enabled = false
- paid_resource_created = false
- main_merge = false
- secret_value_exposed = false
- old_render_postgres_deleted = false

Canonical service:
`crypto-edge-radar-v05-canary`
(`srv-dalqkpu1egvs73fhiehg`)

Canonical branch:
`crypto-edge-radar-postgres-v0.5`

Canonical deployed commit throughout cutover:
`03f0858430fb9aa768410cecc5e8942c970fd4e3`

Supabase target:
`crypto-edge-radar-evidence-v05`

Project ref:
`jqzdvgjeuveiktftyrlz`

Region:
`eu-central-1`

Runtime role:
`radar_runtime`

Session Pooler:
`aws-0-eu-central-1.pooler.supabase.com:5432`

SSL required.

## Credential and pooler discovery

The operator assigned the runtime-role password privately and placed the same secret directly in Render.

Independent metadata verification proved:
`radar_runtime password_set = true`

The password value was never read, logged, committed, written to Drive, or exposed in chat.

Read-only pooler discovery tested the bounded eu-central-1 Session Pooler set and produced exactly one accepted endpoint:

`aws-0-eu-central-1.pooler.supabase.com:5432`

Discovery classification:
`EXACT_SESSION_POOLER_DISCOVERED`

At discovery:
- event_count = 1115
- key_count = 1037
- max_event_id = 1115
- chain_head_sha256 = `d3c5db1ff1e59d7f78b4f1957c85318b9ac20422904442f268c50de0e7c17fe1`

## Authenticated target preflight

Authenticated read-only target preflight:
`TARGET_PREFLIGHT_PASS_BACKUP_PREFIX_CURRENT_CHAIN_OK`

Verified identity:
- database = `postgres`
- role = `radar_runtime`
- server_version_num = `170006`
- sequence exact to max id
- ids contiguous from 1
- chain valid
- no database mutation by preflight

## Final source quiesce

Source writes were frozen using:
`RADAR_EVIDENCE_WRITES_QUIESCED=true`

Observed canonical source runtime after handover:
- mode = `EVIDENCE_WRITES_QUIESCED`
- database_target_mode = `SOURCE`
- maintenance_quiesce = true
- health = `OK`
- chain_verified = true
- event_count = 1117

Final source snapshot:
- event_count = 1117
- key_count = 1039
- max_event_id = 1117
- chain_head_sha256 = `9be022da9832d7630bd064136a1c67a2e0dba28e0cf31674f349552399e094cb`
- canonical_snapshot_sha256 = `70dba28f49eb1a337f5010c1c98ea1311b6efd0eed2eb395b8e7bd4cca5a4930`
- raw_json_sha256 = `1be75dec39aed9c3a8fb69166bf95b9e5c863027628ce28d3234a13b85f1a2c3`
- snapshot chunks = 149/149
- chain_verified = true

Temporary JSON backup-log transport was disabled again after the snapshot.

## Exact-prefix proof

The canonical hash of the final source snapshot restricted to:
- events id <= 1115
- keys whose event_id <= 1115

was independently recomputed as:

`c3b0c7f6cefe80c448cf805c9ff22b4f47792b46eb1fb287e01e368976b7411d`

The authenticated Supabase target snapshot at 1115/1037 had the exact same canonical hash.

Classification:
`SOURCE_PREFIX_EQUALS_TARGET_BYTE_CANONICAL_AT_1115`

This proved exact prefix equivalence, not merely matching row counts.

## Final two-row delta

Final source suffix after the proven 1115 prefix consisted of exactly:

### Event 1116
- type = `RADAR_RUNTIME_LIVENESS`
- key = `RADAR_RUNTIME_LIVENESS:2026-09-27T14:00:00Z`
- prev_chain = `d3c5db1ff1e59d7f78b4f1957c85318b9ac20422904442f268c50de0e7c17fe1`
- chain = `91ba1d9d8608bcd32ea744619920a940fca79822f75f270b1dd3d13a587750f0`

### Event 1117
- type = `ETF_EXEC_V2_PUBLIC_PREFLIGHT`
- key = `ETF-CME-INSTFLOW-001:EXEC-V2:2026-09-27T14`
- prev_chain = `91ba1d9d8608bcd32ea744619920a940fca79822f75f270b1dd3d13a587750f0`
- chain = `9be022da9832d7630bd064136a1c67a2e0dba28e0cf31674f349552399e094cb`

Before any assistant reconciliation insert was executed, the Supabase target was independently observed already at 1117/1039 with rows 1116/1117, keys, hashes and sequence exactly matching the frozen source snapshot.

No assistant insert/update/delete was executed for this delta.

Audit of this observation found:
- no logical subscriptions
- no foreign servers
- no non-internal triggers on evidence tables
- no pg_cron
- no pg_net
- no postgres_fdw
- no dblink
- no other active Render Radar writer among v04/v06/v07/v09 in the audited window

The exact author of the already-present two-row reconciliation was not established. The observation is preserved rather than guessed.

Final pre-switch target identity was independently verified:
- events = 1117
- keys = 1039
- min_id = 1
- max_id = 1117
- chain_head = `9be022da9832d7630bd064136a1c67a2e0dba28e0cf31674f349552399e094cb`
- sequence_last_value = 1117
- sequence_is_called = true

## Quiesced backend switch

With source writes still quiesced, Render was switched using the frozen target configuration.

Quiesced target deploy:
`dep-dasi8tgjo6nc73bt8fog`

Observed live state at 2026-09-27T14:14:10.997240Z:
- database_target_mode = `SUPABASE_POOLER`
- evidence_backend = `postgres`
- evidence_chain_detail = `verified 1117 events via postgres`
- evidence_chain_ok = true
- maintenance_quiesce = true
- mode = `EVIDENCE_WRITES_QUIESCED`
- health = `OK`
- orders_created = false
- exchange_mutation_performed = false
- live_capital_enabled = false

This proved the backend switch before any prospective target write was permitted.

## Prospective resume and chain continuation

Writes were then resumed by setting:
`RADAR_EVIDENCE_WRITES_QUIESCED=false`

Resume deploy:
`dep-dasi9i8jo6nc73btbdt0`

Deploy status:
`live`

First post-cutover prospective append:
- event_id = 1118
- event_type = `RADAR_RUNTIME_LIVENESS`
- event_key = `RADAR_RUNTIME_LIVENESS:2026-09-27T14:15:00Z`
- prev_chain_sha256 = `9be022da9832d7630bd064136a1c67a2e0dba28e0cf31674f349552399e094cb`
- chain_sha256 = `09e07df71b1c44f87893a480eb28494a2f7619c0c251c91f257ea1232513eb0b`
- payload_sha256 = `825e6ae6690ce91ed1665e52d2018fd383b4e5b76efba2c353b1ec78b3d52d28`

Independent Supabase verification after the append:
- event_count = 1118
- key_count = 1040
- max_event_id = 1118
- chain_head_sha256 = `09e07df71b1c44f87893a480eb28494a2f7619c0c251c91f257ea1232513eb0b`
- sequence_last_value = 1118
- sequence_is_called = true

Runtime state:
- database_target_mode = `SUPABASE_POOLER`
- mode = `PUBLIC_SHADOW_ONLY`
- health = `OK`
- evidence_chain_ok = true
- liveness status = `CONTINUOUS`
- authenticated_exchange_api_used = false
- orders_created = false
- exchange_mutation_performed = false
- live_capital_enabled = false

## Old source writer isolation

Render Postgres source:
`dpg-dalqi4qd0e5s738a77kg-a`

Observed active connections for every 30-second sample from 14:13:30Z through 14:17:30Z:
`0`

Therefore the canonical runtime was no longer using the old Render Postgres after target activation.

The old Render Postgres was NOT deleted.

It remains preserved as historical fallback evidence. Because the Supabase target has now advanced prospectively to event 1118 and beyond, rollback is no longer a blind URL flip: any rollback would require explicit reconciliation to the newer target chain.

## Restart and idempotency proof

Pre-restart key check:
`RADAR_RUNTIME_LIVENESS:2026-09-27T14:15:00Z`
- key_rows = 1
- event_id = 1118

Same-commit restart deploy:
`dep-dasibb60tbcc73fhler0`

Restart deploy status:
`live`

New runtime instance:
`srv-dalqkpu1egvs73fhiehg-hibernate-67d469d48c-jhbz9`

Observed after restart:
- database_target_mode = `SUPABASE_POOLER`
- health = `OK`
- evidence_chain_ok = true
- event_count = 1118
- key_count = 1040
- sequence_last_value = 1118
- runtime_liveness.evidence_inserted = false
- runtime_liveness.status = `CONTINUOUS`

Post-restart SQL key check:
- key_rows = 1
- event_id = 1118

Post-restart target identity remained:
- events = 1118
- keys = 1040
- chain_head = `09e07df71b1c44f87893a480eb28494a2f7619c0c251c91f257ea1232513eb0b`
- sequence = 1118 / called=true

Classification:
`RESTART_RECOVERY_AND_APPEND_ONCE_IDEMPOTENCY_PASS`

## Target security after cutover

Supabase security advisor:
`PASS — 0 lints`

Supabase performance advisor:
`PASS — 0 lints`

Dedicated role remains least privilege under the previously frozen role/RLS authority.

## Operational note on telemetry

The runtime's legacy `persistence_expiry` sub-object still contains static pre-cutover labels such as `FINAL_QUIESCED_REFRESH_REQUIRED` and old discovery flags.

Those fields are stale historical telemetry and were not used as cutover authority.

Authoritative runtime routing state is:
`database_target_mode = SUPABASE_POOLER`

No science or evidence rows were altered to correct that telemetry during this cutover.

## Final verdict

**CUTOVER COMPLETE.**

Canonical evidence persistence is now Supabase through the audited Supavisor Shared Session Pooler.

The frozen 1117-event source chain was preserved exactly, the target continued prospectively at event 1118, restart recovery preserved the chain, and append-once idempotency was independently proven.

Old Render Postgres remains intact and non-canonical.

No trading authority, capital authority, scientific promotion, exchange mutation, or main merge is implied by this infrastructure closeout.
