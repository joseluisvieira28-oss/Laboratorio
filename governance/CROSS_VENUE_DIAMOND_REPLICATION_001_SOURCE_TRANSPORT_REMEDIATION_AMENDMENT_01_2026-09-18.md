# CROSS-VENUE-DIAMOND-REPLICATION-001 — SOURCE TRANSPORT REMEDIATION AMENDMENT 01 — 2026-09-18

Status: FROZEN_BEFORE_ANY_SIGNAL_OR_OUTCOME_CALCULATION
Parent freeze: governance/CROSS_VENUE_DIAMOND_REPLICATION_001_DONCHIAN6H_FREEZE_2026-09-18.md
Branch: cross-venue-diamond-replication-001-donchian6h

## Reason for amendment

The first source-coverage receipt returned SOURCE_DATA_BLOCKED without calculating any signal, return, expectancy, PnL, or trading outcome.

Observed transport-only blockers:
- Bybit public V5 requests from the GitHub-hosted runner returned HTTP 403 for all probed endpoints. The runner is hosted in a US Azure region; Bybit officially documents that US-located IP addresses are restricted and return HTTP 403.
- OKX returned valid historical candle responses for multiple frozen symbols/anchors, but the parallel probe triggered HTTP 429 rate limiting. Historical funding requests through the ordinary funding-rate-history endpoint returned no rows for the old anchors and therefore do not establish absence of archived funding.

No market outcome was inspected. No trading rule has changed.

## Frozen remediation

### BYBIT

Allowed transport hosts, in this fixed order:
1. https://api.bybit.com
2. https://api.bytick.com

Both are documented Bybit mainnet V5 endpoints.

The same exact public endpoints, category=linear, symbols, intervals, anchors, and funding requirements remain frozen.

If both official mainnet hosts return environment/geography 403 from the hosted runner, classify:
BYBIT_SOURCE_BLOCKED_ENVIRONMENT

Do not substitute:
- spot
- inverse contracts
- a regional/account-specific host
- mark/index price
- another symbol
- another venue

A future official public-archive transport may be added only by another source-only amendment frozen before archive contents or trading outcomes are inspected.

### OKX

Keep the same exact USDT SWAP instruments and endpoints.

Transport remediation:
- remove cross-symbol parallel flooding for OKX;
- enforce at least 250 ms between OKX REST calls and retry HTTP 429 with bounded backoff;
- preserve 6Hutc and 1m timestamp-anchor checks;
- ordinary funding-rate-history may be used only as a recent-history endpoint and is not authoritative for 2023-2024 archive absence.

Historical archive discovery:
- the official public endpoint /api/v5/public/market-data-history may be probed metadata-only;
- its accepted module enum may be discovered by bounded enumeration of module values 1..10 because the current public documentation/SDK exposes the endpoint signature but the first transport receipt did not bind the archive module mapping;
- module-discovery may inspect only response code/message, metadata keys, file names/URLs, instrument identifiers, and covered date ranges;
- it must not download/read archive payload bytes during the module-discovery stage;
- once a funding archive module is identified from provider metadata, the exact module value and parameterization must be persisted in a new source binding before any archive payload is opened.

This is a source/provenance remediation only.

## Invariants preserved

- candidate DH-02-HO1 6H unchanged
- six-symbol universe unchanged
- 2023-2024 window unchanged
- LONG_ONLY unchanged
- Donchian 80 unchanged
- ATR56 unchanged
- next 6H open entry unchanged
- stop/target/max hold unchanged
- BASE 20 bps / STRESS 30 bps unchanged
- actual venue funding required
- no signals/returns/PnL during source gate
- 2025 and 2026 forbidden
- no venue dropping after outcomes
- no live trading, exchange mutation, orders, wallets, alerts/webhooks, or main merge
