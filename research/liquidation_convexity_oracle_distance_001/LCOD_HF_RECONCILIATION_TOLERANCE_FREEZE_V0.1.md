# LCOD HF RECONCILIATION TOLERANCE FREEZE V0.1

Date: 2026-09-24
Lab: LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001
Stage: SOURCE / MECHANISM
Market outcomes: CLOSED

## Source calibration evidence

V0.1 display-USD reconciliation:
- 47 complete debt-bearing positions;
- relative error median 5.8569e-8;
- p95 0.001093737;
- max 0.013178208;
- large errors concentrated in dust positions because displayed USD component values lose relative precision.

V0.2 raw-component remediation:
- source method: supply balance(main units) * reserve priceUsd * collateralFactorPct; debt=(principal+interest)*priceUsd;
- 35 borrowers sampled;
- 47 complete debt-bearing positions;
- one additional position excluded for required-field incompleteness;
- completeness = 47 / 48 = 97.9167%, above frozen >=90% gate;
- median relative HF error = 3.532621e-6;
- p95 = 2.357332e-5;
- max = 2.999854e-5;
- maximum observed absolute identity error between borrow balance and principal+interest = 5.684342e-14 main units.

No BTC/ETH/crypto return, liquidation outcome or PnL was opened.

## Frozen reconciliation tolerance

Canonical forward component snapshot acceptance rule:

relative_hf_error = abs(reconstructed_hf - official_hf) / official_hf

PASS if:
relative_hf_error <= 5e-5

Equivalent:
<= 0.005% relative error.

Why 5e-5:
- it is above the full 47-position V0.2 calibration maximum 2.999854e-5;
- it is a simple conservative representation/rounding envelope;
- it was frozen from source precision evidence only, before any LCOD market/liquidation outcome.

No wider tolerance may be introduced under LCOD-001 after a failure.

## Source verdict

FORWARD_COMPONENT_SOURCE_RECONCILIATION_PASS

This means:
- current V4 position components can be collected;
- reserve priceUsd and collateralFactorPct can be bound;
- raw principal+interest debt can be reconstructed;
- reconstructed HF is consistent with official Aave health semantics inside the frozen tolerance.

It does NOT mean:
- historical state reconstruction is proven;
- full protocol borrower coverage is proven;
- liquidation prediction is proven;
- market edge exists.

Historical LCOD remains SOURCE_UNPROVEN.
