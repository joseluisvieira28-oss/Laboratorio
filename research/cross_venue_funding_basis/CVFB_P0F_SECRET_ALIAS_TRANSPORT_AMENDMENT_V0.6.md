# CVFB — P0F SECRET-ALIAS TRANSPORT AMENDMENT V0.6

Date: 2026-09-27
Branch: `cross-venue-funding-basis-p0f-final-attack-v0.6`

## Purpose

Permit the already-frozen P0F explorer_blocks requester-pays source-only probe to use an existing repository-scoped AWS credential pair under either of two pre-existing secret name families:

1. `CVFB_P0E_AWS_ACCESS_KEY_ID` / `CVFB_P0E_AWS_SECRET_ACCESS_KEY` / optional session token
2. `L2R_AWS_ACCESS_KEY_ID` / `L2R_AWS_SECRET_ACCESS_KEY` / optional session token

This is a transport-only amendment. It does not authorize creation, disclosure, logging, hashing, export, or modification of any secret.

## Scientific invariants

Unchanged:
- source: `s3://hl-mainnet-node-data/explorer_blocks`
- exact 4 object keys frozen in P0F V0.1A
- zero LIST requests
- max 4 HEAD requests
- max 4 GET requests
- max 32 MiB compressed bytes
- planning cost ceiling USD 0.05
- decoder and schema logic
- no oracle numeric values emitted
- no market numeric values emitted
- no economic outcomes
- primary replication remains closed
- 2026 remains closed
- no live/paper trading
- no exchange mutation
- no main merge
- no tuning

## Credential selection

The runtime may:
- use the CVFB secret family if the mandatory access/secret pair is present;
- otherwise use the L2R secret family if the mandatory access/secret pair is present;
- otherwise fail closed before any S3 request.

The runtime may emit only:
- selected alias family name (`CVFB`, `L2R`, or `NONE`);
- booleans for mandatory credential presence.

It must never emit secret values, prefixes, hashes, lengths, account IDs, or transformed secret material.

## Outcome rule

If credentials are unavailable, the canonical current classification remains:
`PROVENANCE_RECOVERY_BLOCKED_NOT_NO_EDGE`.

If credentials are available, the exact frozen P0F runner must be executed without modification. Its source-only terminal decision remains authoritative for this stage.
