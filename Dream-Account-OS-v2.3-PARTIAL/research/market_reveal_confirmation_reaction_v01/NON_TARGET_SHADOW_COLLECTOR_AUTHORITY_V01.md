# MRCR V0.1 — Non-Target Local Shadow Collector Authority
Status: AUTHORIZED / SOURCE-ONLY / NON-TARGET
Date: 2026-09-24

## Purpose

Prove that a local collector can receive public Coinbase level2 data, timestamp arrival, persist exact raw bytes, hash them, detect duplicates/gaps, survive restart, verify storage integrity and deterministically reconstruct the order book.

This authority is infrastructure-only. It does not authorize scientific target observation.

## Allowed

- public Coinbase Advanced Trade market-data WebSocket only;
- one operator-selected transport fixture product;
- level2 + public heartbeat subscription;
- exact raw WebSocket payload persistence to a local SQLite database;
- collector wall-clock nanoseconds;
- collector monotonic nanoseconds;
- source/envelope timestamps;
- sequence numbers;
- raw SHA-256;
- per-session tamper-evident hash chain;
- duplicate detection;
- SQLite WAL;
- SQLite integrity check;
- deterministic replay/recovery of the venue-native order book;
- sanitized operational receipts.

The transport fixture product is not a frozen scientific target selection and carries zero promotion credit.

## Required local-only boundary

Raw payload storage remains local to the operator machine unless a later authority explicitly permits transfer.

No raw payload upload to GitHub Actions, Drive, Render or an exchange/account endpoint is authorized by this document.

## Forbidden

- macro-event calendar targeting;
- running because a CPI/NFP/FOMC event is imminent;
- acceptance/rejection labels;
- future-return labels;
- PnL;
- entries/exits;
- paper orders;
- live orders;
- account/authenticated endpoints;
- API keys;
- wallets;
- exchange mutation;
- classifier tuning;
- target-horizon selection;
- promotion evidence;
- main merge;
- Render deployment.

## Integrity model

For every persisted delivery the journal stores:

- exact raw payload bytes;
- SHA-256(raw payload);
- collector wall-clock ns;
- collector monotonic ns;
- channel/product/sequence metadata when available;
- previous chain hash;
- current chain hash.

A chain entry is computed from the prior chain hash plus canonical metadata and raw SHA-256. Any later mutation must invalidate verification.

## Recovery model

A recovery pass must:

1. run SQLite integrity_check;
2. verify raw SHA-256 for every row;
3. recompute the per-session hash chain;
4. replay level2 snapshot/update messages in persisted order;
5. fail closed on invalid JSON, missing snapshot, sequence gap or invalid/crossed book;
6. report only sanitized structural diagnostics.

## Anti-contamination rule

Do not schedule the shadow collector around macro announcements or use its contents to select scientific MRCR parameters.

Final boundary:

**PROVE COLLECTION AND RECOVERY; DO NOT TEST EDGE.**
