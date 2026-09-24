# AAVE-HF-CROWDING-001 — CALIBRATION DAY 1 RECEIPT

Date: 2026-09-24
Canonical successful snapshot run: 35980119507
Stage: OUTCOME-BLIND CALIBRATION
Classification: HF_CROWDING_CALIBRATION_COLLECTING

## Technical history

Initial run used an invalid Aave MCP holder limit=5 and opened zero predictor values.
Technical amendment V0.1A changed only the API-schema-invalid limit to the smallest allowed value, limit=10.
No health-factor value or market/liquidation outcome had been opened before the correction.

## Canonical snapshot

- v4 reserves: 92
- sampled deduplicated borrowers: 467
- valid health factors: 467
- valid-HF coverage: 100%
- holder query errors: 0
- summary query errors: 0

Frozen primary predictor:
- fraction HF < 1.10 = **0.2077087794** (20.77%)

Diagnostics only:
- HF < 1.05 = 14.35%
- HF < 1.25 = 32.33%
- median HF = 1.47253445

## Scientific status

This is one calibration snapshot only.
No liquidation outcome, market price, return, volatility or PnL was opened.

Calibration requires >=30 distinct valid UTC-day snapshots with median HF coverage >=80% before the q90 stress threshold may be frozen.

No promotion credit is created by Day 1.
