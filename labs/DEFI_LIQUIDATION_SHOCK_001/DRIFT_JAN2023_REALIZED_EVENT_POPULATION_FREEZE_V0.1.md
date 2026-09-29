# DLS — DRIFT JAN-2023 REALIZED-EVENT POPULATION FREEZE V0.1

Date: 2026-09-29
Status: FROZEN BEFORE POPULATION SIGNED-FLOW EXTRACTION
Branch: dls-signed-flow-authority-v01

## Why this freeze exists

The preceding 3-reference calibration run 36525100147 is preserved as
DRIFT_SIGNED_SEMANTICS_CALIBRATION_BLOCKED: 2/3 references had exactly bound,
non-zero LiquidationRecord events and one successful liquidate_perp instruction
had no decodable LiquidationRecord.

Existing pre-calibration route evidence for that third reference shows
`max_base_asset_amount_allowed_to_be_transferred == 0` and no realized
LiquidationRecord. Therefore a successful liquidate_perp instruction is not
automatically a realized liquidation event.

This is a population-unit correction, not a threshold change and not a rescue
based on market outcomes. No prices or returns were opened.

## Frozen population

Input is exactly the already-open canonical Drift January-2023 field-enrichment
partition:
- run 36264543005
- artifact dls-field-enrichment-drift-drift-202301
- artifact ID 10915721179
- digest sha256:47c9f1af96c29c2c7ea80f2a167d27c932932f956ae8b650a5388cb9b14730c8
- interval 2023-01-01T00:00:00Z <= timestamp < 2023-02-01T00:00:00Z
- class liquidate_perp

Every canonical liquidate_perp instruction is queried. It enters the
SIGNED-FLOW FAMILY DENOMINATOR only if the exact successful transaction contains
an exactly bound Drift LiquidationRecord of type LiquidatePerp for the canonical
liquidated_user, liquidator, and perp_market_index.

A successful instruction with no exactly bound LiquidationRecord is classified
NO_REALIZED_LIQUIDATION_RECORD and excluded from the realized-event denominator.
It is still counted and reported in the census.

A transaction/query/identity failure that prevents determining whether a
realized event exists is SOURCE_EVIDENCE_INCOMPLETE and is NOT silently excluded.

## Frozen signed rule

For each exactly bound realized event, using the historical January-2023 Drift
semantics frozen in DRIFT_JAN2023_SIGNED_FLOW_SEMANTICS_CALIBRATION_FREEZE_V0.1.md:

- signed base_asset_amount < 0 => SIGNED_SELL_PRESSURE_PROVEN
- signed base_asset_amount > 0 => SIGNED_BUY_PRESSURE_PROVEN
- signed base_asset_amount == 0 => DIRECTION_AMBIGUOUS

No price or subsequent market outcome is used.

## Family adjudication

Let R = number of realized events.
Let I = realized events whose required source evidence is incomplete.
Let D = realized events with a unique deterministic non-zero direction.
Let A = realized events that are direction ambiguous.
Let C = contradictions.

SIGNED_FLOW_AUTHORIZED for Drift January-2023 only if:
1. R > 0;
2. (R-I)/R >= 0.95;
3. D/(R-I) >= 0.90;
4. C == 0;
5. rule is exclusively transaction/program semantics.

Otherwise classify:
- SIGNED_FLOW_SOURCE_PARTIAL if defensible realized signed evidence exists but
  family thresholds are not met;
- SIGNED_FLOW_SOURCE_BLOCKED if source evidence cannot support a defensible
  realized-event census.

This is a protocol/class source authority result only. It authorizes at most a
future separately frozen signed-return experiment.

## Firewall

prices=false
returns=false
pnl=false
2025_market_outcomes=false
2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
post_outcome_tuning=false
