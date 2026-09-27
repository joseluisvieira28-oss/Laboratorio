# DEFI-LIQUIDATION-SHOCK-001 — GLOBAL FIELD COVERAGE FINAL GATE VERSION PRECEDENCE ADDENDUM V0.4

Date: 2026-09-27
Status: FROZEN TECHNICAL ADJUDICATION RULE / SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Supersede earlier receipt precedence only where newer source-only authorities now exist.
No PASS criterion, protocol universe, event population, or economic rule is changed.

## Kamino + Save11 field precedence

Highest first:
1. KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.3.json
2. KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.2.json
3. KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.1.json

When V0.3 exists it is authoritative. A V0.3 BLOCKED receipt may not be bypassed by V0.2/V0.1.
Global PASS still requires KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_PASS and exact frozen totals:
- Kamino 60,699
- Save11 13,300
- zero required missing/extra/duplicate/semantic-conflict counts.

## Kamino + Save11 unit precedence

Highest first:
1. KAMINO_SAVE11_UNIT_METADATA_POPULATION_RECEIPT_V0.4.json
2. KAMINO_SAVE11_UNIT_METADATA_POPULATION_RECEIPT_V0.3.json
3. KAMINO_SAVE11_UNIT_METADATA_POPULATION_RECEIPT_V0.2.json
4. KAMINO_SAVE11_UNIT_METADATA_POPULATION_RECEIPT_V0.1.json

When V0.4 exists it is authoritative. A V0.4 BLOCKED receipt may not be bypassed by V0.3/V0.2/V0.1.
Global PASS still requires KAMINO_SAVE11_UNIT_METADATA_POPULATION_PASS, every event unit-complete, and zero required unit conflicts.

## Retained precedence

- Save0c units: V0.3 > V0.2 > V0.1.
- Marginfi Bank: V0.2 > V0.1.
- Drift market units: temporal V0.3 authority.
- Marginfi + Save0c field: V0.1.

## Global fail-closed rule

Artifact/receipt version selection occurs before scientific classification adjudication.
The highest frozen authority present is selected even when its classification is BLOCKED.
An older PASS can never override a newer BLOCKED authority.

Economic outcomes remain closed.

## Firewall

prices=false
usd_notional=false
returns=false
pnl=false
direction=false
economic_outcomes=false
token_amounts=false
requested_amount_values=false
realized_transfer_amounts=false
trailing_byte_value_emitted=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
post_outcome_tuning=false
merge_main=false
