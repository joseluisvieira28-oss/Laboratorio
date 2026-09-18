# AAVE-RISK-PARAMETER-SHOCK-001 — PRIMARY MECHANISM CENSUS CLOSEOUT V0.1

Date: 2026-09-18
Status: TERMINAL FOR EXACT PRIMARY MECHANISM / NO DISCOVERY / NO RESCUE

## Final classification

INSUFFICIENT_PRIMARY_MECHANISM_SAMPLE

This is not NO_EDGE.
No liquidation outcome, market return or PnL was opened.

## Canonical source lineage

Source Census V0.1A:
- run: 35382293497
- artifact: 10563606987
- classification: SOURCE_CENSUS_PASS
- total structural events: 749
- CollateralConfigurationChanged events: 72

Primary Mechanism Census V0.1A:
- run: 35385465168
- artifact: 10564642712
- artifact digest: sha256:2dd51e13db15e531bc8d1132a6bad5e62012efba7ed2a941cffc05accfa7220d
- classification: INSUFFICIENT_PRIMARY_MECHANISM_SAMPLE

## Frozen primary mechanism

Only:
new liquidationThreshold < immediately previous in-envelope liquidationThreshold for the same asset.

No BorrowCap, SupplyCap, ReserveFrozen, ReservePaused, DebtCeiling or other configurator event family may replace it after census inspection.

## Exact census result

- decoded configuration-history events: 72
- primary liquidationThreshold-decrease logs: 16
- primary decrease transaction clusters: 5
- independent 24-hour episodes: 5
- unique affected assets: 12
- calendar years represented: 2023 and 2024

Frozen sample gates:
- independent 24-hour episodes >= 12: FAIL (5)
- unique affected assets >= 4: PASS (12)
- calendar years >= 2: PASS (2)

The exact primary mechanism therefore fails the prospectively frozen independence/sample requirement.

## Adjudication

STOP before Discovery.

Do NOT:
- lower the 12-episode minimum;
- redefine independence;
- split transaction clusters;
- threshold by magnitude;
- select only particular assets;
- switch to another configurator event family;
- change years;
- open LiquidationCall outcomes;
- open market prices/returns/PnL.

A materially different protocol-risk mechanism would require a new LAB_ID and new prospective freeze.

## Safety

No borrower state opened.
No health factor computed.
No liquidation-overhang predictor computed.
No future LiquidationCall outcomes opened.
No market prices opened.
No returns opened.
No PnL opened.
No 2025/2026 accessed.
No live trading.
No exchange mutation.
No main merge.
