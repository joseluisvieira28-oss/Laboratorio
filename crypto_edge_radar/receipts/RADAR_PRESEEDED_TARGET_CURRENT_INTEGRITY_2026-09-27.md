# CRYPTO EDGE RADAR — PRESEEDED TARGET CURRENT INTEGRITY RECEIPT — 2026-09-27

Status: **TARGET CURRENTLY EXACT-CHAIN-VALID / CUTOVER CREDENTIAL BLOCKED**

## Canonical source observation

Render canary heartbeat observed after the 2026-09-27 backup refresh:
- runtime commit: `d4762b70b673daada386276467ea5be2796018e1`
- health: `OK`
- evidence chain: `verified 1036 events via postgres`
- errors: none
- orders: false
- exchange mutation: false
- live capital: false
- authenticated exchange API: false

## Supabase target current verification

Project: `crypto-edge-radar-evidence-v05`
Project ref: `jqzdvgjeuveiktftyrlz`
Status: `ACTIVE_HEALTHY`

Server-side deterministic verification:
- event count: 1036
- min id: 1
- max id: 1036
- distinct ids: 1036
- payload SHA256 mismatches: 0
- previous-chain mismatches: 0
- chain SHA256 mismatches: 0
- chain head: `97d9ec08e6b55dfcb44f4bbd1460c815509349599ed2ddf60533bedf4b85209c`
- event keys: 958
- orphan keys: 0
- duplicate keys: 0
- BIGSERIAL sequence last value: 1036

Event 1033 has `prev_chain_sha256=f8b85ba3...`, exactly matching the independently verified source-backup chain head at event 1032. Events 1033..1036 form a valid continuation.

This proves target internal integrity and continuity from the frozen 1032 backup boundary. It does not independently prove current source/target rowset equality for all 1036 rows because the Render source is not externally queryable and the current private backup hook is disabled. Final V0.1/V0.2 quiesced snapshot equivalence remains mandatory before switch.

## Security

Supabase security advisor: no findings.
Supabase performance advisor: no findings.
Both public evidence tables have RLS enabled. No credential is stored in this receipt.

## Remaining blocker

Canonical runtime reports:
`TARGET_CONNECTION_CREDENTIAL_NOT_CONFIGURED`

Supabase documentation requires the actual Connect-provided connection string and database password. Render is documented as IPv4-only for this path, so the shared session pooler is the appropriate persistent-backend route unless network capability is independently proven otherwise. The pooler host must not be guessed from region/project metadata.

No DATABASE_URL switch was attempted.

## Governance

Authority: `RADAR_POSTGRES_CUTOVER_PROTOCOL_V0.1.md` plus proposed `RADAR_POSTGRES_CUTOVER_PRESEEDED_TARGET_AMENDMENT_V0.2.md`.

No science changes. No outcome changes. No trading. No orders. No wallets. No exchange mutation. No capital. No main merge.
