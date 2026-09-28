# DLS — DRIFT LIQUIDATION EVENT LOG ROUTE CALIBRATION FREEZE V0.1

Date: 2026-09-28
Status: FROZEN SOURCE-ONLY MICRO-CALIBRATION

## Population source

Canonical Drift field-enrichment partition:
- run 36264543005
- artifact dls-field-enrichment-drift-drift-202301
- artifact ID 10915721179
- classification FIELD_ENRICHMENT_PARTITION_PASS

## Deterministic references

From liquidate_perp events only, rank by ascending SHA256 of:
signature || "|" || JSON-canonical instructionAddress

Select first 3.

## Query

For each exact slot, request:
- all transactions with signature/error;
- all logs with programId, message, kind, transactionIndex, instructionAddress.

Bind the exact transaction by frozen signature.
Keep only logs with that transactionIndex.

## PASS

DRIFT_LIQUIDATION_EVENT_LOG_ROUTE_3_OF_3_PASS if:
- exact canonical transaction recovered for all 3;
- each has >=1 Drift-program log/data item;
- identity conflicts = 0.

This does not yet decode or assign direction.

## Firewall

prices=false
returns=false
direction=false
2025_market_outcomes=false
2026_market_outcomes=false
live_trading=false
orders=false
merge_main=false
