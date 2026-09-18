# ETH-STAKING-FLOW-001 — HISTORICAL BEACON ARCHIVE TRANSPORT PROBE V0.3

Status: PRE-ACQUISITION FROZEN / SOURCE-ONLY
Date: 2026-09-18
Branch: eth-staking-flow-v0.3-archive-probe
Family: ETH-STAKING-FLOW-001
Parent economic MVE: ESF-NETQUEUE-7D-001

## Purpose

Recover the ORIGINAL V0.1 standard-Beacon-API source representation without changing its scientific definition. This probe asks only whether a currently reachable no-key public Beacon API can serve historical validator-state queries at both frozen source boundaries.

No ETH/BTC market prices, signal values, returns, PnL or 2025/2026 source states may be opened.

## Original frozen semantics preserved

Window: 2023-04-12 through 2024-12-31.
Daily observation: first canonical consensus state at or after 00:00:00 UTC, with deterministic fallback through +32 slots only.
Variables:
- pending_queued validator count
- active_exiting validator count
- net_queue_count = pending_queued - active_exiting

Standard route:
GET /eth/v1/beacon/states/{slot}/validators?status=pending_queued
GET /eth/v1/beacon/states/{slot}/validators?status=active_exiting

## Prospectively frozen public transport candidates

Ordered independently of outcomes, from public documentation/current ecosystem references:

1. https://lodestar-mainnet.chainsafe.io
2. http://testing.mainnet.beacon-api.nimbus.team
3. https://ethereum-beacon-api.publicnode.com
4. https://rpc.ankr.com/eth_beacon
5. https://eth-mainnetbeacon.g.alchemy.com/v2/docs-demo

A provider passes only if BOTH boundary dates can each resolve one candidate slot within +0..32 for BOTH frozen status filters, with valid JSON validator arrays and no authentication/payment response.

Provider fallback is transport-only. The first passing provider in frozen order becomes eligible for a separate full-source V0.3 gate. This probe itself does not authorize Discovery.

## Retained probe outputs only

- HTTP status
- response byte count
- SHA256
- selected slot and offset if successful
- returned validator-row count for schema/availability proof
- auth/technical classification

Queue values are source-structure facts only and must not be joined to ETH prices.

## Classifications

ARCHIVE_TRANSPORT_PROBE_PASS
ARCHIVE_TRANSPORT_PROBE_BLOCKED
ARCHIVE_TRANSPORT_PROBE_TECHNICAL_FAILURE
PROVENANCE_FAILURE

## Firewall

2025_accessed=false
2026_accessed=false
ETH/BTC prices=false
signal series=false
Discovery event count=false
returns=false
PnL=false
performance=false
live trading=false
exchange mutation=false
wallet access=false
merge to main=false
