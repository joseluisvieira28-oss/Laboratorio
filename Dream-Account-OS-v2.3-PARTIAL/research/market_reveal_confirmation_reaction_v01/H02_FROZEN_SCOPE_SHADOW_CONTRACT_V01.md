# MRCR H02 — Frozen-Scope Shadow Hardening Contract V0.1
Status: SOURCE-INFRASTRUCTURE ONLY / TARGET OBSERVATION LOCKED
Date: 2026-09-26
LAB_ID: MARKET-REVEAL-CONFIRMATION-REACTION-001
H02_ID: MRCR-H02-ACCEPTANCE-REJECTION-V01

## Purpose

Harden the exact already-frozen H02 public market-data scope before any future
target observation can be opened.

This package is not a target collector. It has no event calendar, target-event
scheduler, classifier invocation, future-return computation, economics or
execution path.

## Immutable source scope

Binance Spot:
- BTCUSDT aggTrade;
- BTCUSDT diff depth@100ms + public REST depth snapshot;
- ETHUSDT aggTrade;
- ETHUSDT diff depth@100ms + public REST depth snapshot.

Coinbase Advanced Spot:
- BTC-USD level2;
- BTC-USD market_trades;
- ETH-USD level2;
- ETH-USD market_trades.

No asset, venue, symbol or channel outside this set is accepted by the canonical
launcher.

## Session isolation

The batch contains six independent sessions:

1. Binance BTCUSDT trades+depth.
2. Binance ETHUSDT trades+depth.
3. Coinbase BTC-USD level2.
4. Coinbase BTC-USD market_trades.
5. Coinbase ETH-USD level2.
6. Coinbase ETH-USD market_trades.

Coinbase channels are intentionally isolated so sequence continuity is evaluated
inside a single subscribed public feed instead of assuming cross-channel
sequence semantics.

## Binance synchronization contract

For each symbol:

1. open public market-data WebSocket;
2. immediately begin buffering/persisting diff-depth messages;
3. fetch the public REST depth snapshot;
4. persist the exact snapshot bytes and update ID;
5. offline recovery discards stale diffs;
6. the first useful diff must bridge snapshot_last_update_id + 1;
7. every later gap fails closed.

This follows the public Binance local-order-book synchronization contract.

## Persistence contract

Local SQLite journal:
- WAL;
- synchronous FULL;
- foreign keys ON;
- busy timeout;
- exact raw payload bytes;
- SHA-256 per raw payload;
- per-session tamper-evident hash chain;
- source time min/max where available;
- collector UTC wall-clock ns;
- collector monotonic ns;
- sequence/update identifiers;
- idempotent duplicate handling.

Raw payloads remain local. Upload is not authorized by this contract.

## Restart/recovery contract

The launcher performs two distinct phases:

1. collect and close all six sessions;
2. start an independent offline verifier process that reopens SQLite and
   reconstructs/validates the latest batch.

PASS requires:

- SQLite integrity PASS;
- exact six-session frozen scope;
- all six terminal statuses PASS;
- every hash chain PASS;
- Binance snapshot bridge/replay PASS on BTCUSDT and ETHUSDT;
- Coinbase level2 sequence/replay PASS on BTC-USD and ETH-USD;
- Coinbase market_trades sequence/schema replay PASS on BTC-USD and ETH-USD.

Any missing session, sequence gap, invalid snapshot bridge, missing Coinbase
snapshot, raw tamper, metadata tamper or replay failure => FAIL_CLOSED.

## Hard boundaries

Always false:
- authentication_used;
- account_endpoints_used;
- signals_computed;
- outcomes_computed;
- orders_enabled;
- target_schedule_used;
- target_observation_authorized.

Scientific use:
SOURCE_INFRASTRUCTURE_HARDENING_ONLY.

Promotion credit:
NONE.

This contract does not alter H02_SCIENTIFIC_RULESET_V01, does not issue
TARGET_OBSERVATION_OPEN, and does not permit live or paper trading.
