# EMA6H — T+1 ARCHIVE RECOVERY SIDECAR V0.1 — CLOSEOUT — 2026-09-27

Status: **COMPLETE / DEPLOYED / LIVE / T+1 RECOVERY PATH VALIDATED**

Classification:
`EMA6H_ARCHIVE_RECOVERY_V0.1_COMPLETE__FULL_WARMUP_EQUIVALENCE_AND_LIVE_IDEMPOTENCY_PASS`

## Mission scope

Operational source resilience only.

- scientific rules changed = false
- thresholds changed = false
- outcomes changed = false
- universe changed = false
- timeframe changed = false
- signal rule changed = false
- authenticated exchange API used = false
- orders created = false
- exchange mutation performed = false
- live capital enabled = false
- paid resource created = false
- repository main merged = false

## Original blocker

Canonical Render Frankfurt runtime was rate-limited by Binance public REST.

Observed canonical runtime before integration:
- EMA6H status = WAITING_SOURCE_RATE_LIMIT
- HTTP status = 418
- server ban until = 2026-09-27T20:45:59.987000Z
- REST retry not before = 2026-09-27T20:46:59.987000Z

A multi-host official REST failover was investigated and rejected.

GitHub Actions:
- data-api.binance.vision responded
- api.binance.com / api-gcp / api1-api4 returned HTTP 451
- the >=2-host exact-equivalence gate failed closed

Render Frankfurt:
- all seven tested official REST hosts returned HTTP 418
- no REST-host failover was promoted

Classification:
`OFFICIAL_REST_HOST_FAILOVER_SOURCE_BLOCKED`

## Static official archive discovery

The same Frankfurt environment could reach Binance static public-data archive CHECKSUM endpoints at data.binance.vision.

This created a separate T+1 recovery lane rather than weakening the REST gate.

Archive safety:
- .CHECKSUM SHA256 required before parsing
- Spot archive microsecond timestamps normalized explicitly to milliseconds
- only open_time, OHLC, volume and close_time are supplied to the frozen science
- incomplete requested ranges fail closed
- overlapping archive data must be identical
- same-day archive recovery is forbidden
- monthly files are used for completed months
- daily files are used for current-month T+1 tail
- in-memory archive-period cache avoids repeated downloads

## Exact REST vs archive equivalence

Daily proof for 2026-09-26:

BTCUSDT 15m:
- REST rows = 96
- archive rows = 96
- exact scientific fields = true
- SHA256 = `74b16dd770034125a11c348342a3f4b53f9674fe448ff513deb1dd178fd3f6a3`

SOLUSDT 15m:
- REST rows = 96
- archive rows = 96
- exact scientific fields = true
- SHA256 = `dc8021b6f84fca52f4a6c9584d0fc212e872844cafc4da579c52d99ea9f2dcd5`

Classification:
`PASS_REST_ARCHIVE_EXACT_EQUIVALENCE`

## Full frozen warmup equivalence

The exact ranges required by the frozen EMA6H science were compared.

BTCUSDT 15m — 60 days:
- REST rows = 5760
- archive rows = 5760
- exact scientific fields = true
- all archive checksums verified = true
- SHA256 = `c2a8c3872349dbdbd162dc4f893ba923439700cddd2fbbdd209305e0cc3f1811`

SOLUSDT 15m — 60 days:
- REST rows = 5760
- archive rows = 5760
- exact scientific fields = true
- all archive checksums verified = true
- SHA256 = `66e2bd3cffb73c2bc4ecd928167539b70b1dc42da55a92edb536095ec6223c7e`

BTCUSDT 1d — 240 days:
- REST rows = 240
- archive rows = 240
- exact scientific fields = true
- all archive checksums verified = true
- SHA256 = `f9f9a1a20890670a5c3ff4cda421b0f5d67c854b08ba1efd75fcb16fac4bbc09`

Classification:
`PASS_FULL_FROZEN_WARMUP_EXACT_EQUIVALENCE`

## Sidecar design

Sidecar:
`EMA6H-50X200-REGIME-ARCHIVE-RECOVERY-V0.1`

Provider:
`BINANCE_PUBLIC_DATA_KLINES_RECOVERY_V0.2`

The sidecar reuses the canonical frozen `EMA6HRegimeForwardWatcher`. It does not reimplement EMA, regime, entry, signal or resolution science.

Activation:
- runs only while primary EMA6H status is WAITING_SOURCE_RATE_LIMIT
- primary REST remains authoritative for same-day data
- archive recovery is T+1 only
- successful archive recovery sleeps until the next UTC day + 15 minutes
- archive unavailable / fail-closed states use a separate 30 minute backoff

## QA

Integration PR:
`#154 — EMA6H — T+1 archive recovery sidecar V0.1`

Feature head:
`0a9ef24afddee58781329268316cb190e2d86fd8`

All 11 integration/regression checks passed:
- EMA6H ARCHIVE RECOVERY V0.1 QA
- Radar Forward Once Manual V0.1
- Radar Binance 418 Cooldown V0.1 QA
- BNB Diamond V0.2 Sidecar QA
- Radar Database Target Mode Telemetry V0.1 QA
- Radar Supabase Pooler Discovery V0.1 QA
- OPTIONS V2.1 Public Execution Shadow V0.1 QA
- CED1D Archive Pending Retry V0.4 QA
- Radar Supabase Target Preflight V0.2 QA
- Radar Evidence Identity V0.1 QA
- CED1D Render Shadow Migration V0.3 QA

PR #154 was squash-merged into the canonical operational Radar branch only.

Canonical deployed commit:
`b9d8e28ff0ec0fe8a67cc9e1970e8c1050c2fa36`

No merge to repository main was performed.

## Render deployment

Canonical service:
`crypto-edge-radar-v05-canary`

Service ID:
`srv-dalqkpu1egvs73fhiehg`

Deploy:
`dep-dasn8160tbcc73860k2g`

Deployment status:
`live`

Finished:
`2026-09-27T19:54:00.618504Z`

## Live runtime proof

Observed live runtime:
- git commit = b9d8e28ff0ec0fe8a67cc9e1970e8c1050c2fa36
- health = OK
- mode = PUBLIC_SHADOW_ONLY
- database_target_mode = SUPABASE_POOLER
- persistence watchdog = PASS_CANONICAL_SUPABASE_SINGLE_WRITER
- persistence failures = []
- primary EMA6H = WAITING_SOURCE_RATE_LIMIT
- primary HTTP status = 418
- archive sidecar = ARCHIVE_RECOVERY_OK
- archive recovery cutoff signal close = 2026-09-26T18:00:00Z
- scientific cutoff = 2026-09-26T23:59:59.999000Z
- same_day_recovery_allowed = false
- sidecar canonical watcher status = OK
- sidecar missing boundaries = 0
- sidecar new boundaries = 0
- sidecar inserted signals = 0
- sidecar inserted resolutions = 0
- sidecar evidence_advanced = false
- science_changed = false
- outcomes_changed = false
- orders_created = false
- exchange_mutation_performed = false
- live_capital_enabled = false
- runtime errors = {}

No archive files needed to be downloaded in this live cycle because every boundary through the T+1 cutoff was already present. Therefore archive_period_receipts = 0 and archive_all_checksums_verified = null, correctly avoiding a false claim of checksum verification for a cycle that performed no archive reads.

## Independent Supabase proof

Independent read-only SQL after deployment:
- events = 1145
- keys = 1067
- min_id = 1
- max_id = 1145
- sequence_last_value = 1145
- sequence_is_called = true
- chain head = `e80c36e6f04a4197c25bec0f0b58e49cb35ead4d330730ec2cb0fcd8d5828fe7`

Independent EMA6H event census:
- EMA6H_REGIME_FORWARD_BOUNDARY = 29
- no signal or resolution event type exists in the census

This matches the live metrics:
- boundaries audited = 29
- signals = 0
- resolved forward crosses = 0
- rule deviations = 0

Classification:
`LIVE_ARCHIVE_SIDECAR_IDEMPOTENCY_PASS__NO_FABRICATED_EVIDENCE`

## Scientific state after mission

EMA6H remains scientifically:
- FORWARD_EVIDENCE_ACCUMULATING
- first review progress = 0/10
- strong review progress = 0/25
- automatic promotion = false
- live trading authorized = false

This mission improved source resilience only. It did not produce or imply scientific edge.

## Final verdict

**EMA6H T+1 ARCHIVE RECOVERY SIDECAR V0.1 = COMPLETE / LIVE / VALIDATED.**

The remaining current-day dependency is legitimate:
same-day EMA6H boundaries still require the primary public REST path, and the ban-aware runtime will not retry it before the server-derived retry deadline.

The archive sidecar is now available to recover eligible T+1 gaps without changing frozen science and without fabricating evidence.
