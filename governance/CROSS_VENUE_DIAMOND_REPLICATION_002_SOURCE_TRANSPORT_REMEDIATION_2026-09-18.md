# CROSS-VENUE-DIAMOND-REPLICATION-002 — SOURCE TRANSPORT REMEDIATION ADDENDUM — 2026-09-18

Status: FROZEN_TRANSPORT_REMEDIATION_ONLY

This addendum is frozen before any AVAX20 cross-venue outcome calculation.

Reason:
The sibling Donchian cross-venue source probe demonstrated shared-runner transport fragility: Bybit HTTP 403 on api.bybit.com and OKX HTTP 429 under concurrent access. The AVAX20 branch therefore adopts the same transport hardening before adjudicating source coverage.

Authorized remediation only:
1. serialized source requests;
2. 0.15 second shared-IP throttle plus retry backoff;
3. Bybit official-mainnet host fallback api.bybit.com -> api.bytick.com;
4. preserve AVAXUSDT / AVAX-USDT-SWAP, 1m trade-price source, funding history, frozen 2024-09 warmup + calendar-2025 replication block, and metadata-only Stage-A receipt.

No candidate identity, signal implementation, direction, lookback, horizon, costs, sample rules, venue set, or outcome rule changes.
No 2026+ access. No live trading, authenticated exchange APIs, orders, wallets, exchange mutation, execution webhooks, or main merge.
