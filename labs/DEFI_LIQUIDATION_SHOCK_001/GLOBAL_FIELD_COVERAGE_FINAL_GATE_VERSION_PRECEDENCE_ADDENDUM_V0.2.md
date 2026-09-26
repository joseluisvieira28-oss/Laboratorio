# DEFI-LIQUIDATION-SHOCK-001 — GLOBAL FIELD COVERAGE FINAL GATE VERSION PRECEDENCE ADDENDUM V0.2

Date: 2026-09-26
Status: FROZEN TECHNICAL ADJUDICATION RULE / SOURCE-ONLY / OUTCOME-BLIND

## Purpose

The original Global Field Coverage Final Gate froze terminal scientific classifications before conditional source-completion paths existed.

This addendum defines deterministic receipt-version precedence only.
It does not weaken any PASS criterion and does not alter the frozen event population.

## Authorized receipt precedence

### Save0c unit metadata

Authorized candidates, highest first:
1. SAVE0C_UNIT_METADATA_POPULATION_RECEIPT_V0.3.json
2. SAVE0C_UNIT_METADATA_POPULATION_RECEIPT_V0.2.json
3. SAVE0C_UNIT_METADATA_POPULATION_RECEIPT_V0.1.json

The highest version present is authoritative only if its trigger chain is valid.

Global PASS still requires:
SAVE0C_UNIT_METADATA_POPULATION_PASS

For V0.3 additionally require:
- still_unmapped_event_count = 0
- unique_still_unmapped_reserve_count = 0
- pending_reserve_count = 0
- source_conflict_count = 0
- event_conflict_count = 0
- error_count = 0

For V0.2 additionally require the equivalent unresolved/pending/conflict counts = 0.

A V0.1 PARTIAL may be superseded by a valid later PASS.
A later BLOCKED result cannot be bypassed by selecting an older PASS/PARTIAL receipt.

### Marginfi bank unit registry

Authorized candidates, highest first:
1. MARGINFI_BANK_UNIT_REGISTRY_RECEIPT_V0.2.json
2. MARGINFI_BANK_UNIT_REGISTRY_RECEIPT_V0.1.json

Global PASS still requires:
MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS

For V0.2 additionally require:
- still_unmapped_bank_count = 0
- pending_account_count = 0
- conflict_count = 0
- error_count = 0

A V0.1 PARTIAL may be superseded by a valid V0.2 PASS.
A V0.2 BLOCKED result is authoritative fail-closed.

## Other families

No version precedence change:
- KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.1.json
- MARGINFI_SAVE0C_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.1.json
- DRIFT_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.1.json
- KAMINO_SAVE11_UNIT_METADATA_POPULATION_RECEIPT_V0.1.json
- DRIFT_MARKET_UNIT_REGISTRY_POPULATION_RECEIPT_V0.1.json

## Global rule

Receipt selection is plumbing only.

Terminal PASS remains possible only when every mandatory family/classification is PASS and every required unresolved/missing/conflict/pending/guessed count is zero.

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
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
