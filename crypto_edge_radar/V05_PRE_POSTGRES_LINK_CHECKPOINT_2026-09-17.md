# CRYPTO EDGE RADAR — V0.5 PRE-POSTGRES-LINK CHECKPOINT — 2026-09-17

Status: **CODE_AND_RENDER_CANARY_PASS / POSTGRES_LINK_PENDING**

## GitHub authority

- Repository: `joseluisvieira28-oss/Laboratorio`
- Branch: `crypto-edge-radar-postgres-v0.5`
- Current code commit: `8ebe18c5eee525cc771f062c0442e09841f4dffe`
- GitHub Actions run: `35202325129`
- Offline safety tests: PASS
- Public shadow soak: PASS
- Packaged runtime installation: PASS
- Postgres evidence-chain unit tests: PASS
- SQLite fallback: PASS

## Render V0.5 canary

- Service: `crypto-edge-radar-v05-canary`
- Service ID: `srv-dalqkpu1egvs73fhiehg`
- Region: `frankfurt`
- Plan: `free`
- Auto-deploy: `off`
- Python: `3.12.14`
- Final deploy ID: `dep-dalqmpm7bikc73a906bg`
- Deployed commit: `8ebe18c5eee525cc771f062c0442e09841f4dffe`
- Deploy status: LIVE
- Build tests on Render: 37/37 PASS

First real runtime heartbeat from the new instance `srv-dalqkpu1egvs73fhiehg-mbbnf`:

- completed_at_utc: `2026-09-17T08:58:04.823644Z`
- health: `OK`
- mode: `PUBLIC_SHADOW_ONLY`
- provider: `BINANCE_SPOT_DATA_API_PUBLIC`
- evidence_backend: `sqlite`
- evidence_event_id: `3`
- evidence_chain_sha256: `20f7b70a54230732d5eaed9d8a32eac267ab178f699e3619aca1af0cff704c30`
- registered_strategies: `0`
- valid_signal_count: `0`
- consecutive_failures: `0`

The SQLite backend is intentional until a Render secret links the remote datastore. No claim of Postgres persistence is made yet.

## Validation Postgres

- Render Postgres ID: `dpg-dalqi4qd0e5s738a77kg-a`
- Name: `crypto-edge-radar-evidence-v04`
- Region: `frankfurt`
- PostgreSQL: `18`
- Plan: `free`
- Status: `available`
- Expires: `2026-10-17T08:47:15.2559Z`

This database is a 30-day persistence validation/soak datastore, not permanent production storage.

## Remaining gate

The Render connector does not expose the database password/internal connection URL and cannot create a secret linked from this Postgres instance. Therefore one dashboard action is required:

1. Copy the Postgres **Internal Database URL** from its Connect panel.
2. Add it to service `crypto-edge-radar-v05-canary` as environment variable `RADAR_DATABASE_URL`.
3. Save/deploy.

Do not paste the connection URL into chat.

After that action, the acceptance proof is three consecutive real runtime heartbeats showing:

- `health=OK`
- `evidence_backend=postgres`
- non-null `evidence_event_id`
- non-null `evidence_chain_sha256`
- `registered_strategies=0`
- `valid_signal_count=0`

Only then may V0.5 be classified as `POSTGRES_PERSISTENCE_CANARY_PASS / 30_DAY_SOAK_READY`.

No main merge, live trading, authenticated exchange API, order path, wallet access, or real-money execution is authorized by this checkpoint.
