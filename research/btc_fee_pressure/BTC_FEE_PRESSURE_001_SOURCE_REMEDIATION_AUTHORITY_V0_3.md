# BTC-FEE-PRESSURE-001 — SOURCE-REMEDIATION AUTHORITY V0.3

Status: FROZEN PRE-ACQUISITION / OUTCOME-BLIND  
Date: 2026-09-14 UTC  
Drive authority ID: `1Q1M6qpDJ73wwxZtNgyfBxLCbhmUmRsrSmFVtbUTHx78`  
Lineage: V0.2 = `TECHNICAL_FAILURE_PREOUTCOME` after GitHub Actions timeout at 120 minutes. No source verdict or artifact was emitted.

## Immutable scientific MVE
`BFP-TOTALFEES-7D-001`. Daily total BTC transaction fees paid to miners in canonical blocks assigned to UTC day, excluding coinbase reward. Future trigger: strictly above trailing 90-observation 80th percentile excluding day t. LONG BTC, next UTC daily open, hold 7 days, no overlap, 10 bps base / 20 bps stress.

## Window
2021-01-01T00:00:00Z through 2024-12-31T23:59:59Z only.

## Source semantics — unchanged
Read-only mempool.space canonical historical block route. Required fields remain block id/hash, height, timestamp and `extras.totalFees`. Boundary timestamps remain pre-2025. Blockstream Esplora remains provenance/audit fallback only. No market-price, USD, exchange, current-mempool, fee-estimate or write endpoints.

## Authorized technical changes only
1. Remove overlapping block-batch requests by detecting and stepping the endpoint's contiguous batch width.
2. Use bounded parallel acquisition of independent historical batches.
3. Preserve deterministic full-height reconciliation and fail closed on any missing height, conflicting hash, malformed block or incomplete day.
4. Increase workflow runtime ceiling only to prevent infrastructure timeout.
5. Preserve raw response bytes, request URLs, manifests and SHA256 evidence.

## Gate — unchanged
Require >=1,400 UTC days; unique canonical heights/hashes; finite non-negative fees; explicit missing/duplicate/malformed report; no fill/interpolation. Valid terminal states: `SOURCE_DATA_PASS`, `SOURCE_AUTH_BLOCKED`, `SOURCE_ACQUISITION_TECHNICAL_FAILURE`, `DATA_FAILURE`, `PROVENANCE_FAILURE`, `INSUFFICIENT_SAMPLE`.

## Firewall
2025 LOCKED. 2026 LOCKED. No market prices, returns, PnL, Discovery, live trading, exchange mutation, merge to main or post-outcome tuning.

## Routing
If V0.3 reaches `SOURCE_DATA_PASS`, STOP and require a separate prospective pre-Discovery authority before opening outcomes. If V0.3 fails technically or at source/provenance/data gates, do not rescue this MVE again; preserve the terminal classification and advance to a genuinely new #18 mechanism.
