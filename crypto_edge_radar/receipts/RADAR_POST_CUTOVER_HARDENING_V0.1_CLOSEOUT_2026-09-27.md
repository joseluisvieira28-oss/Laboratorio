# CRYPTO EDGE RADAR — POST-CUTOVER HARDENING V0.1 — CLOSEOUT — 2026-09-27

Status: **COMPLETE / DEPLOYED / LIVE / FAIL-CLOSED PERSISTENCE ROUTE HARDENED**

Classification:
`RADAR_POST_CUTOVER_HARDENING_V0.1_COMPLETE__CANONICAL_SUPABASE_SINGLE_WRITER_PASS`

## Scope

Operational persistence hardening only.

- science_changed = false
- outcomes_changed = false
- thresholds_changed = false
- trading_authority_changed = false
- authenticated_exchange_api_used = false
- orders_created = false
- exchange_mutation_performed = false
- live_capital_enabled = false
- paid_resource_created = false
- main_merge = false
- old_render_postgres_deleted = false
- secrets_exposed = false

## Canonical runtime

Service:
`crypto-edge-radar-v05-canary`

Service ID:
`srv-dalqkpu1egvs73fhiehg`

Branch:
`crypto-edge-radar-postgres-v0.5`

Canonical hardening commit:
`2395bde1e285316446998096507caaef22abfa73`

Deployment:
`dep-dasj6p0jo6nc73c16t80`

Deployment status:
`live`

Deployment finished:
`2026-09-27T15:18:31.116656Z`

## QA

Feature PR:
`#146 — Radar — post-cutover persistence hardening V0.1`

Feature head before squash:
`91b075347e2b71a0002e9ef53581cc83db0ec318`

Dedicated deterministic QA:
`RADAR POST-CUTOVER HARDENING V0.1 QA`

Final-head run:
`36328869586`

Result:
`SUCCESS`

The final PR head also completed the existing Radar checks successfully, including:

- Radar Database Target Mode Telemetry V0.1 QA
- Radar Supabase Pooler Discovery V0.1 QA
- Radar Evidence Identity V0.1 QA
- Radar Supabase Target Preflight V0.2 QA
- Radar Forward Once Manual V0.1
- Radar Binance 418 Cooldown V0.1 QA
- OPTIONS V2.1 Public Execution Shadow V0.1 QA
- BNB Diamond V0.2 Sidecar QA
- CED1D Render Shadow Migration V0.3 QA
- CED1D Archive Pending Retry V0.4 QA

PR #146 was squash-merged into the canonical Radar operational branch only.
It was NOT merged to repository main.

## Persistence watchdog

New runtime authority:
`RADAR_PERSISTENCE_WATCHDOG_V0.1`

Observed live classification:
`PASS_CANONICAL_SUPABASE_SINGLE_WRITER`

Observed live state:

- pass = true
- writes_allowed = true
- enforcement_required = true
- canonical_render_service = true
- database_target_mode = `SUPABASE_POOLER`
- canonical target provider = `SUPABASE`
- canonical project ref = `jqzdvgjeuveiktftyrlz`
- target flag enabled = true
- pooler host configured = true
- runtime credential configured = true
- target URL configured = true
- secret_value_exposed = false
- failures = []

The watchdog executes before watcher/liveness writes. A failed canonical persistence route returns:
`PERSISTENCE_ROUTE_FAIL_CLOSED`

and the service does not start scientific/scheduler worker threads.

Therefore the canonical service can no longer silently fall back to the historical SOURCE route under the hardened runtime.

## Corrected post-cutover telemetry

Observed live persistence classification:
`CUTOVER_COMPLETE_CANONICAL_SUPABASE`

Observed live operational authority:
`POST_CUTOVER_RUNTIME_TRUTH`

The stale pre-cutover runtime story is no longer authoritative.

Observed corrected fields:

- cutover_complete = true
- migration_required = false
- cutover_blocker = null
- final_quiesced_refresh_required = false
- final_cutover_authorized = true
- cutover_authority_consumed = true
- target_pooler_host_discovered = true
- target_connection_credential_configured = true
- target_url_configured = true
- rollback_blind_url_flip_allowed = false
- rollback_requires_reconciliation = true
- historical source role = `NON_CANONICAL_ROLLBACK_ONLY`

The old target preflight receipt remains visible for history but is explicitly marked:
`HISTORICAL_PRE_CUTOVER_RECEIPT_ONLY`

and:
`superseded_by = RADAR_PERSISTENCE_WATCHDOG_V0.1`

## Independent post-deploy target proof

Independent Supabase SQL after the hardened deployment:

- events = 1123
- keys = 1045
- min_id = 1
- max_id = 1123
- chain_head_sha256 = `a49188c0e734b18472bb0a4aa3b0e8485c22509f3c91b554506410b0b1e3619b`
- sequence_last_value = 1123
- sequence_is_called = true

Live watchdog integrity proof independently reported the same:

- event_count = 1123
- key_count = 1045
- max_event_id = 1123
- chain_head_sha256 = `a49188c0e734b18472bb0a4aa3b0e8485c22509f3c91b554506410b0b1e3619b`
- key_binding_sha256 = `ba13e015b236246cedbdc4b74328de8153fb4166b0a1e60b1f0a240f55fccb5d`
- sequence_last_value = 1123
- sequence_is_called = true
- chain_verified = true

Classification:
`INDEPENDENT_TARGET_IDENTITY_MATCH`

## Current writer observation

Independent `pg_stat_activity` observation after deployment showed:

- role = `radar_runtime`
- application_name = `Supavisor`
- sessions = 1

This supports the expected single canonical runtime session at the observed instant.

It is an observation, not a claim that PostgreSQL can never show another transient/system connection.

## Historical Render source

Historical Render Postgres:
`dpg-dalqi4qd0e5s738a77kg-a`

Canonical classification:
`NON_CANONICAL_ROLLBACK_ONLY`

It remains intact.

During the hardened deployment window, active-connections samples from 15:16:30Z through 15:20:00Z were all:
`0`

Earlier audit window 14:20Z–15:20Z contained one transient active-connection sample at 14:40Z, followed by zero again.

No evidence tied that transient connection to a Radar writer.

Classification:
`TRANSIENT_CONNECTION_OBSERVED__NO_OLD_RADAR_WRITER_EVIDENCE`

No attempt was made to delete or mutate the historical Postgres.

## Old Render Radar services

Audited legacy services:

- `crypto-edge-radar-canary-v04`
- `crypto-edge-radar-v06-etf-cme-canary`
- `crypto-edge-radar-v07-control-room-canary`
- `crypto-edge-radar-v09-forward-preflight`

All have autoDeploy disabled.

They are NOT claimed to be administratively suspended: Render reports them as not suspended and the available connector does not expose a safe suspend/scale-to-zero action.

Observed application logs for all four from 15:00Z through 15:21Z:
`0`

Earlier audit from 14:20Z through 15:20Z also showed:
`0` old-service logs.

Classification:
`DORMANT_AUTODEPLOY_OFF__NO_RUNTIME_ACTIVITY_OBSERVED`

No old service was awakened or redeployed merely to test it.

## Runtime safety

Observed live hardened runtime:

- health = `OK`
- database_target_mode = `SUPABASE_POOLER`
- persistence watchdog = `PASS_CANONICAL_SUPABASE_SINGLE_WRITER`
- evidence chain verified = true
- authenticated_exchange_api_used = false
- orders_created = false
- exchange_mutation_performed = false
- live_capital_enabled = false

## Dashboard

The read-only Radar cockpit now surfaces:

- persistence watchdog classification
- target mode
- event / key counts
- max event ID / sequence
- historical source role

This removes the previous ambiguity where correct Supabase routing coexisted with stale pre-cutover telemetry.

## Final verdict

**POST-CUTOVER HARDENING V0.1 COMPLETE.**

The canonical Radar is live on Supabase with:

1. a pre-write fail-closed persistence route guard,
2. a canonical-service / single-writer guard,
3. periodic secret-safe chain and sequence integrity proof,
4. corrected post-cutover telemetry,
5. historical preflight clearly marked non-authoritative,
6. historical Render Postgres explicitly classified as `NON_CANONICAL_ROLLBACK_ONLY`,
7. deterministic tests and existing Radar regression checks passing.

No scientific candidate, threshold, outcome, promotion state, execution authority or capital authority was changed by this mission.
