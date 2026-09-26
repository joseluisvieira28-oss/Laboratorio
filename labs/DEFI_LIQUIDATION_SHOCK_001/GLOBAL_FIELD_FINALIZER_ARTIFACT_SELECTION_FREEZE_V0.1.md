# DEFI-LIQUIDATION-SHOCK-001 — GLOBAL FIELD FINALIZER ARTIFACT SELECTION FREEZE V0.1

Date: 2026-09-26
Status: FROZEN TECHNICAL SELECTION / SOURCE-ONLY / OUTCOME-BLIND

## Purpose

Freeze how the Global Field Coverage finalizer locates terminal evidence artifacts after all required families have been adjudicated.

Artifact selection is version plumbing only. It MUST NOT select based on favorable scientific values.

## Fixed artifact names

Mandatory single-version artifacts:
- dls-marginfi-save0c-field-enrichment-population-v01
- dls-kamino-save11-field-enrichment-population-v01
- dls-drift-field-unit-final-v03
- dls-kamino-save11-unit-metadata-population-v01

Save0c unit metadata precedence, highest authorized version first:
1. dls-save0c-unit-metadata-source-completion-v03
2. dls-save0c-unit-metadata-source-completion-v02
3. dls-save0c-unit-metadata-population-v01

Marginfi bank unit precedence:
1. dls-marginfi-bank-unit-source-completion-v02
2. dls-marginfi-bank-unit-registry-v01

## Selection rule

For each logical family:
1. query GitHub Actions artifacts by the exact frozen artifact name;
2. reject expired artifacts;
3. prefer the newest artifact for that exact name;
4. for versioned families, stop at the first available artifact in the frozen precedence list;
5. extract without modifying receipt content.

No artifact may be selected by inspecting its PASS/FAIL result first.

## Launch rule

The finalizer marker may be created only after the watch has independently observed terminal required family classifications consistent with the frozen Global Field Gate.

The finalizer itself re-adjudicates the downloaded receipts and may still fail closed.

## Terminal output

Only the existing adjudicator may emit:
GLOBAL_FIELD_COVERAGE_FINAL_PASS

Otherwise it must remain pending or blocked according to the frozen gate.

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
