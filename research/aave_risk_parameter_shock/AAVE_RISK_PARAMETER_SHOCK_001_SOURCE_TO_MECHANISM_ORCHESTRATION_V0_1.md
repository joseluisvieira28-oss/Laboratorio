# AAVE-RISK-PARAMETER-SHOCK-001 — SOURCE TO MECHANISM CENSUS ORCHESTRATION V0.1

Date: 2026-09-18
Status: FROZEN BEFORE PRIMARY-MECHANISM VALUE DECODING

## Exact source upstream

Canonical technical-remediation candidate:
- workflow run: 35382293497
- head SHA: 0620b6d20a3a2d5b3d9be3fc6f3ac5b2b669bcdf
- workflow: AAVE Risk Parameter Shock 001 — Source Census V0.1A
- expected artifact: AAVE_RISK_PARAMETER_SHOCK_001_SOURCE_CENSUS_V0_1A

This upstream is the prospectively prepared sparse-window remediation. It changes transport handling only: a healthy zero-match configurator window is covered with zero events rather than treated as a source failure.

## Gate

Proceed only if the exact source receipt is:
SOURCE_CENSUS_PASS

Any source technical/provenance/insufficient verdict stops this orchestration.

## Authorized next step

Execute only:
research/aave_risk_parameter_shock/primary_mechanism_census_v01.py

This census may decode only the already-frozen:
CollateralConfigurationChanged(address,uint256,uint256,uint256)

Primary mechanism remains:
new liquidationThreshold < immediately previous in-envelope liquidationThreshold for the same asset.

Independence gate remains the prospectively frozen fixed 24-hour episode grouping:
- >=12 independent episodes
- >=4 affected assets
- >=2 UTC calendar years

No magnitude threshold.
No event-family substitution.
No borrower state.
No LiquidationCall outcomes.
No market prices/returns/PnL.
No 2025/2026.
No live trading/exchange mutation/main merge.

## Terminal states

MECHANISM_CENSUS_PASS:
permits only the already-frozen contingent pre-Discovery protocol to be considered under its activation/authority gate.

INSUFFICIENT_PRIMARY_MECHANISM_SAMPLE:
close this exact primary mechanism as insufficient sample. Do not rescue with another configurator event family.

Any technical/provenance failure:
stop and preserve exact cause.
