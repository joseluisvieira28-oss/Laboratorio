# TVSQZ-001 — TECHNICAL SUPERSESSION RECEIPT 01

Date: 2026-09-23
State: SUPERSEDED_PRE_OUTCOME
Affected run: GitHub Actions run 35915438713

## Failure boundary
The first execution failed inside actions/checkout before repository checkout, Python setup, source acquisition, indicator computation, event construction, or market-outcome evaluation.

Observed failure:
`server certificate verification failed. CAfile: none CRLfile: none`

## Scientific equivalence
No scientific field is changed:
- LAB_ID remains TVSQZ-001.
- Universe, source family, dates, symbols, timeframe and protected periods remain unchanged.
- Squeeze definition and parameters remain unchanged.
- Stage A/B outcomes, gates, bootstrap rules, costs, sample thresholds and decision rules remain unchanged.
- 2024, 2025 and 2026 remain unopened.

## Plumbing correction
Before actions/checkout, configure Git to use the runner's system CA bundle:
`/etc/ssl/certs/ca-certificates.crt`.

This receipt exists solely to preserve the pre-outcome technical supersession chain required by Governance V4.
