# BTC-FEE-PRESSURE-001 — SOURCE-REMEDIATION AUTHORITY V0.2

Status: FROZEN PRE-ACQUISITION / OUTCOME-BLIND  
Date: 2026-09-14 UTC  
Lineage: V0.1 DATA_FAILURE. Only the source route changes.

## Immutable MVE
BFP-TOTALFEES-7D-001. Daily total BTC transaction fees paid to miners in canonical blocks assigned to UTC day, excluding coinbase reward. Future trigger: strictly above trailing 90-observation 80th percentile excluding day t. LONG BTC, next UTC daily open, hold 7 days, no overlap, 10 bps base / 20 bps stress.

## Window
2021-01-01T00:00:00Z through 2024-12-31T23:59:59Z only.

## Remediation route
Read-only mempool.space open-source backend:
- GET /api/v1/mining/blocks/timestamp/{unix_timestamp}
- GET /api/v1/blocks/{start_height}

Resolve boundary heights only from frozen pre-2025 timestamps. Traverse canonical block batches deterministically by height. Required fields: id/hash, height, timestamp, extras.totalFees.

Audit route, read-only Blockstream Esplora:
- GET /api/block-height/{height}
- GET /api/block/{hash}

Reject market-price/USD fields. Do not use current mempool, fee estimates, exchange APIs or writes. Probe start/mid/end before bulk acquisition. Preserve raw bytes, headers, manifests and SHA256.

## Gate
Require at least 1,400 UTC days; unique canonical heights/hashes; non-negative finite fees; explicit missing/duplicates/malformed report. No fill.

Valid terminal states: SOURCE_DATA_PASS, SOURCE_AUTH_BLOCKED, SOURCE_ACQUISITION_TECHNICAL_FAILURE, DATA_FAILURE, PROVENANCE_FAILURE, INSUFFICIENT_SAMPLE.

Discovery, prices, returns, PnL, 2025, 2026, live trading and exchange mutation remain prohibited.
