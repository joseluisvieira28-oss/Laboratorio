# CRYPTO EDGE RADAR — POSTGRES EVIDENCE PORTABILITY V0.1

Date: 2026-09-22
Status: PRE-CUTOVER MIGRATION TOOLING / NO TARGET CREDENTIAL YET

## Motivation

The canonical Render Free Postgres instance reports expiry at 2026-10-17T08:47:15.2559Z.
A verified private backup exists, but backup alone does not provide continuous persistence after expiry.

## Goal

Provide a vendor-neutral, fail-closed restore/cutover primitive for a standard PostgreSQL target without changing evidence semantics.

## Required target

- standard PostgreSQL compatible;
- TLS-capable connection;
- sufficient persistent storage;
- supports BIGSERIAL, UNIQUE constraints, foreign keys and transactional DDL/DML;
- target database must be empty of Radar evidence rows before restore.

## Frozen restore semantics

The restore input is a previously verified Radar evidence snapshot containing:
- radar_events rows in exact id order;
- radar_event_keys rows;
- source chain head;
- source snapshot SHA256.

Before any target write:
1. recompute every payload SHA256;
2. recompute every prev-chain binding;
3. recompute every chain SHA256;
4. ensure all event-key references resolve;
5. verify event_count/key_count and chain head.

Target write:
- create schema only if absent;
- reject a target containing any Radar event/key rows;
- insert exact event ids and exact stored hashes;
- insert exact idempotency keys;
- set the BIGSERIAL sequence to the maximum restored event id;
- verify target rows and chain before commit;
- rollback on any mismatch.

## Cutover firewall

This tool does NOT switch DATABASE_URL.
This tool does NOT stop/start the Radar service.
This tool does NOT authorize dual writes.
A real cutover requires a separately frozen maintenance/cutover step ensuring no source events are created between the final source snapshot and DATABASE_URL switch.

## Credential handling

Target URL is read only from RADAR_MIGRATION_TARGET_URL.
Never print, hash, persist or commit the URL.
No target credential = AUTH_REQUIRED_NOT_EXECUTED.

## Governance

source_database_mutation=false
science_changed=false
signals_changed=false
outcomes_changed=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
capital=false
main_merge=false
