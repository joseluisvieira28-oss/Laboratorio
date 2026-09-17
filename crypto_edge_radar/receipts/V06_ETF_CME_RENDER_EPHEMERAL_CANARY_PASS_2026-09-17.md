# CRYPTO EDGE RADAR V0.6 — ETF-CME Render Ephemeral Canary Receipt

Date: 2026-09-17
Status: EPHEMERAL_CANARY_PASS / POSTGRES_LINK_PENDING

## Identity
- Branch: `crypto-edge-radar-etf-cme-v0.6`
- Commit: `3f70c406a0381348c0dffe5207a835335c689f07`
- Render service: `crypto-edge-radar-v06-etf-cme-canary`
- Render service ID: `srv-dals3cmk1f9s7399o200`
- Render deploy ID: `dep-dals3d6k1f9s7399o2m0`
- Region: Frankfurt
- Runtime: Python 3.12.14
- Mode: `PUBLIC_SHADOW_ONLY`

## Registered strategy
Exactly one strategy is registered:
- `ETF-CME-INSTFLOW-001`
- promotion status: `PROMOTED_SHADOW`
- frozen symbol: BTCUSDT
- CFTC public source only
- no authenticated exchange API
- no order endpoint
- no order creation
- no micro-live authorization
- no late-entry chasing

## CI gate
GitHub Actions run `35210829559` passed:
- offline safety tests: PASS
- public-data bounded soak: PASS
- evidence hash-chain verification: PASS (9 events)
- final registered strategy count: exactly 1
- valid signal count at current observation time: 0

Artifact:
- ID: `10491742380`
- SHA256: `3dc8f9607421ddd327a9a0af6aac6ae520794e4ab850f7fc364f67ae5c2a8bd5`

## Render runtime gate
Three consecutive heartbeats on the same instance `srv-dals3cmk1f9s7399o200-4grmr`:

1. cycle 1 — health OK; evidence backend sqlite; event_id 3; registered_strategies 1; valid_signal_count 0; chain `cad9abf43ef39750b5712a21ea755662c8579f5d0634b11679923678d5efd38c`
2. cycle 2 — health OK; evidence backend sqlite; event_id 6; registered_strategies 1; valid_signal_count 0; chain `0cfb0c4f044a7f740f02793231b65969539272859de02e5ae1e24b28e0f34039`
3. cycle 3 — health OK; evidence backend sqlite; event_id 9; registered_strategies 1; valid_signal_count 0; chain `5c9ed4d366f2360aaa2bf37c40b5bdb510f5db46df7d3440bfe54c6be19366fc`

Provider on all three cycles: `BINANCE_SPOT_DATA_API_PUBLIC`.
Consecutive failures: 0.

## Current ETF-CME time-state
The public CFTC receipt observed the latest available current observation as-of 2026-09-08 and a positive frozen signal, but its information-safe exact entry time was 2026-09-16T00:00:00Z. At the V0.6 validation time that entry window had passed, therefore the correct state was `ENTRY_WINDOW_PASSED_DO_NOT_CHASE` and no valid shadow entry signal was emitted.

## Limits / next gate
This receipt proves the V0.6 application/runtime and strategy binding on ephemeral SQLite only. It does NOT establish durable evidence persistence for V0.6. The existing Render Postgres can be reused only after `RADAR_DATABASE_URL` is linked to this V0.6 service and a new three-heartbeat Postgres canary passes.

No live trading, no authenticated exchange access, no orders, no exchange mutation, no merge to main.
