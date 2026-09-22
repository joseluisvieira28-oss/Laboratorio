# CRYPTO EDGE RADAR — POSTGRES CUTOVER PROTOCOL V0.1

Date: 2026-09-22
Status: **FROZEN BEFORE TARGET PROVISIONING**

## Purpose

Move the canonical append-only evidence store from the expiring Render Free Postgres instance to a persistent standard PostgreSQL target without losing, duplicating, rewriting or reordering evidence.

## Preconditions

All must hold:
1. target provider/account is legitimately authorized;
2. target connection URL is supplied only through a secret environment variable;
3. target Radar evidence tables are absent or contain zero events/keys;
4. latest source chain verifies;
5. a fresh pre-cutover private backup is created and independently verified;
6. validated portability tooling remains byte-identical to the approved version;
7. no target is accepted solely because it is reachable.

## Maintenance boundary

The actual cutover must use a short write-quiescence window.

During that window:
- stop new Radar evidence writes before taking the final source snapshot;
- do not alter scientific clocks or reconstruct missed exact-time events;
- take final source snapshot;
- independently verify payload hashes, chain links, key references and head hash;
- restore exact rows to target;
- verify target event count, key count, snapshot hash and chain head equal the final source snapshot;
- only then change the canonical DATABASE_URL;
- redeploy;
- verify health + Postgres backend + chain head on the new target;
- resume normal shadow evidence collection prospectively.

If an exact-time scientific observation falls inside the maintenance window and cannot be observed under its frozen timing rule, record it according to that strategy's existing missed/no-chase policy. Never reconstruct it later to hide the maintenance gap.

## Rollback

Before first new target-only evidence write:
- rollback may point DATABASE_URL back to the untouched source store if target verification fails.

After target-only evidence begins:
- do not blindly switch back to the stale source.
- treat rollback as a new reconciliation problem and fail closed until chain continuity is proven.

## Exact restore invariants

Must preserve:
- event id
- event_ts
- event_type
- payload_json bytes/text
- payload_sha256
- prev_chain_sha256
- chain_sha256
- every (event_type,event_key,event_id) binding
- BIGSERIAL next-id continuity

No reserialization of payload_json is allowed during restore.

## Secrets

Never print or persist:
- source DB URL
- target DB URL
- passwords
- provider tokens

## Governance

No trading.
No orders.
No wallets.
No exchange mutation.
No capital.
No signal/rule/threshold/cost/timing changes.
No automatic promotion.
No main merge.
