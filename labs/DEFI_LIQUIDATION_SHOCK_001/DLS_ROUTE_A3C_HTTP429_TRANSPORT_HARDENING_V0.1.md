# DLS ROUTE A3C — HTTP 429 TRANSPORT HARDENING V0.1

Date: 2026-10-03
Status: TECHNICAL TRANSPORT CORRECTION / SCIENCE UNCHANGED
Branch: dls-field-enrichment-v01

## Observed failure
Run 36996339648 returned SHARD_SOURCE_BLOCKED for all Kamino May shards before any full page was accepted.
Representative immutable shard receipt:
- shard 0 artifact 11222045789
- error: rpc_transport_exhausted:http_429
- full_pages: 0
- full_transaction_count: 0
- market_data_read: false
- economic_outcomes_opened: false

This is transport throttling, not source absence and not a scientific result.

## Correction
Only transport pacing/retry behavior changes:
- shard execution serialized: max-parallel 1
- pre-request pacing: 1.25 seconds
- retry attempts: 12
- HTTP 429 respects Retry-After when present
- exponential backoff capped at 120 seconds
- request timeout 120 seconds

Unchanged:
- exact four frozen protocol classes
- Kamino discriminator/account semantics
- May 2025 shard boundaries
- gTFA full-history route and filters
- limit 1000
- canonical RAW normalizer
- source window
- SOL target mint
- 60-second clustering
- finalizer
- strategy direction/timing/cost/statistical gates
- protected 2025/2026 market-outcome firewall

No prices, returns, PnL, orders, wallets, exchange mutation or main merge.
Trading authority: NONE.
