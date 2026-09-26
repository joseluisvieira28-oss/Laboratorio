# DEFI-LIQUIDATION-SHOCK-001 — GLOBAL FIELD FINALIZER ARTIFACT SELECTION ADDENDUM V0.2

Date: 2026-09-27
Status: FROZEN SOURCE-ONLY ARTIFACT PRECEDENCE

This addendum extends GLOBAL_FIELD_FINALIZER_ARTIFACT_SELECTION_FREEZE_V0.1.md.

## Kamino + Save11 field group

Artifact precedence:
1. dls-kamino-save11-field-enrichment-population-v02
2. dls-kamino-save11-field-enrichment-population-v01

V0.2 is mandatory when present because it implements the source-proven Kamino historical ABI split frozen in:
- KAMINO_HISTORICAL_ACCOUNT_LAYOUT_ADDENDUM_V0.2.md
- KAMINO_LAYOUT_RECOVERY_PRECEDENCE_ADDENDUM_V0.2.md

## Kamino + Save11 unit group

Artifact precedence:
1. dls-kamino-save11-unit-metadata-population-v02
2. dls-kamino-save11-unit-metadata-population-v01

A later V0.2 BLOCKED receipt cannot be bypassed by selecting V0.1.

## Existing precedence retained

Save0c unit:
V0.3 > V0.2 > V0.1

Marginfi Bank:
V0.2 > V0.1

Drift field/unit:
V0.3 temporal final path.

## Selection rule

Version selection is based only on frozen authority/version precedence and artifact existence.
It must not inspect scientific PASS/FAIL before choosing the highest authorized version.

## Firewall

prices=false
returns=false
pnl=false
economic_outcomes=false
protected_2025_2026_market_outcomes=false
post_outcome_tuning=false
merge_main=false
