# MRCR V0.1 — Local Coinbase L2 Shadow Runbook
Status: PASS OPERATOR WINDOWS / NON-TARGET / SOURCE-ONLY
Date: 2026-09-25

## Objective

Use the operator Windows machine/network to prove the public Coinbase level2 path and the complete local persistence/recovery chain.

This is not an MRCR edge test.

## Before running

Do not intentionally schedule this run around CPI, NFP, FOMC or another macro announcement.

Use an ordinary non-event period.

No Coinbase login, API key or account connection is required.

## One-click run

From the checked-out MRCR branch, open:

`Run_MRCR_Coinbase_L2_Shadow.cmd`

The launcher:

1. creates/reuses a local Python virtual environment;
2. installs pinned `websockets==15.0.1`;
3. stores the journal under:
   `%LOCALAPPDATA%\MRCR\shadow_v01\data\coinbase_l2_shadow.sqlite3`;
4. connects only to the public Coinbase market-data WebSocket;
5. subscribes only to level2 for the transport fixture product;
6. uses direct no-proxy WebSocket transport with a bounded 16 MB message ceiling and runs for 60 seconds;
7. persists exact raw source messages locally;
8. runs the offline verifier immediately after collection.

## Required PASS

The collector receipt must show:

- `status = PASS`
- `transport = PASS`
- `subscription_ack = true`
- `l2_snapshot_seen = true`
- `sequence_anomaly = false`
- `chain_integrity_pass = true`
- `recovery_pass = true`
- `authentication_used = false`
- `account_endpoints_used = false`
- `signals_computed = false`
- `outcomes_computed = false`
- `orders_enabled = false`

The following offline verifier must also print `status = PASS`.

## Re-verify later without reconnecting

Open:

`Verify_MRCR_Shadow_Journal.cmd`

This does not connect to Coinbase.

It re-runs:

- SQLite integrity_check;
- raw SHA-256 verification;
- per-session hash-chain verification;
- raw-only order-book reconstruction.

## What to share back

Share only the sanitized JSON receipts printed by:

- the collector;
- the offline verifier.

Do **not** upload or paste:

- the SQLite database;
- WAL/SHM files;
- raw WebSocket payloads.

The raw journal is intentionally local infrastructure evidence.

## Failure handling

If the collector returns FAIL-CLOSED:

- preserve the sanitized receipt;
- do not modify scientific parameters;
- do not interpret failure as NO_EDGE;
- classify the failure by transport / schema / sequence / integrity / recovery;
- re-run only after an objective environment or implementation correction.

If the collector PASSes but offline verification FAILs, treat this as a persistence/recovery defect and do not promote the source path.

## Scientific boundary

BTC-USD in this launcher is a transport fixture, not a frozen MRCR scientific target.

This run cannot authorize:

- H02;
- target observation;
- target asset/venue selection;
- classifier thresholds;
- future-return horizon;
- PnL;
- trading.

Final rule:

**LOCAL SOURCE PASS IS INFRASTRUCTURE EVIDENCE, NOT EDGE EVIDENCE.**


## Operator-host PASS receipt

Sanitized operator evidence:

- session: `424dcd73-dc4c-4d6c-80fd-290dba53d4c9`
- collector: `PASS`
- offline verifier: `PASS`
- transport: `PASS`
- subscription ACK: `true`
- L2 snapshot: `true`
- persisted messages: `999`
- L2 update messages: `997`
- recovered final sequence: `998`
- sequence anomaly: `false`
- SQLite integrity: `true`
- hash-chain integrity: `true`
- raw-only recovery: `true`
- authentication/account endpoints/signals/outcomes/orders: all `false`

### Sequence semantics established on operator host

The observed stream contained global WebSocket sequence continuity across both
`l2_data` and `subscriptions` messages. Therefore L2-only sequence numbers
may appear to skip when an intervening non-L2 message consumes the sequence.

The fail-closed rule is now:

1. require exact continuity across the complete persisted WebSocket stream;
2. allow an apparent L2-only skip only when every intervening sequence number
   is present in the same tamper-evident journal;
3. fail closed on any true full-stream discontinuity.

This receipt establishes local source/persistence/recovery infrastructure only.
It does not authorize H02, target observation, scientific promotion or trading.
