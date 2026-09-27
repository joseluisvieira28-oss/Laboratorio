# CRYPTO-INDEX-REBALANCE-FLOW-001 — BINANCE SOURCE COVERAGE CLOSEOUT V0.1

Date: 2026-09-27
Status: SOURCE_COVERAGE_PASS
Branch: crypto-index-rebalance-flow-v0.1
Draft PR: #144

## Technical pre-run
Run 36329914764 failed before any Binance request because the normalization identity hash included generated_at_utc.
Technical amendment 001 replaced that unstable hash with a stable event-set identity. No scientific or source rule changed.

## Successful execution
Workflow: Bitwise Binance Source Coverage
Run ID: 36330006396
Job ID: 108650002873
Conclusion: SUCCESS
Artifact ID: 10935551728
Artifact ZIP SHA256: 0b3c016585f3c445dfa455d1df3e9aeae95359646da13177a5c73a7ff465a2f5

Stable source-eligibility set SHA256:
0d4b35b68a1a119c91db45b5454d6856afc79b6e7e6018304d7b66030ccc723c

## Gate result
SOURCE_COVERAGE_PASS.

- Normalized 2022-2024 event legs: 69
- Eligible exact-source event legs: 68
- Excluded exact-source event legs: 1
- Eligible rebalance dates: 26
- Eligible years: 2022, 2023, 2024
- Eligible ADD: 34
- Eligible REMOVE: 34
- zero 2025 market requests
- zero market response body bytes read
- ZIP + CHECKSUM existence required for token and BTC across D-1/D/D+1.

## Frozen source exclusion
2024-09-29 / MATIC / REMOVE / MATICUSDT

Reason:
The exact official Binance Vision MATICUSDT 1m ZIP and CHECKSUM are unavailable for 2024-09-28, 2024-09-29 and 2024-09-30 (HTTP 404), coinciding with the historical market transition period.

No POL substitution, alternate venue, alias or nearest source is permitted.

## Scientific meaning
Historical 2022-2024 market-outcome Discovery is source-feasible under the exact frozen event geometry.

No price values or returns were opened by this gate.
2025 market outcomes remain sealed.
