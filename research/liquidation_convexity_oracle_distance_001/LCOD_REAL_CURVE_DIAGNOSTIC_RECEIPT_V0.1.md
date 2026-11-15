# LCOD REAL CURVE DIAGNOSTIC RECEIPT V0.1 — ZERO PROMOTION CREDIT

Date: 2026-09-24
Input: LCOD_HF_RECONCILIATION_V02_RECEIPT.json
Scope: 47 source-complete debt positions from 35 sampled borrowers
Market/liquidation outcomes opened: NO

## Integrity note

The shock grid itself was frozen before source outcomes in SOURCE_GATE_V0.1:
0, -0.25%, -0.50%, -0.75%, -1%, -1.5%, -2%, -3%, -5%.

The uniform-all-collateral / debt-static diagnostic aggregation was stated in the operator session immediately before computation but was not separately durable-committed before the calculation.
Therefore this diagnostic receives ZERO scientific promotion credit and may not be used to choose a trading rule.

## Diagnostic

Uniform proportional shock applied to every collateral capacity term; debt held static.

| Shock | New positions HF<1 | Newly eligible debt USD | Cumulative eligible debt USD |
|---:|---:|---:|---:|
| 0% | 0 | 0 | 0 |
| -0.25% | 0 | 0 | 0 |
| -0.50% | 0 | 0 | 0 |
| -0.75% | 0 | 0 | 0 |
| -1.00% | 0 | 0 | 0 |
| -1.50% | 0 | 0 | 0 |
| -2.00% | 0 | 0 | 0 |
| -3.00% | 1 | 304,030.890823 | 304,030.890823 |
| -5.00% | 0 additional | 0 additional | 304,030.890823 |

Lowest reconstructed HF in the sample:
1.0288133660 with debt 304,030.890823 USD.

Its mechanical uniform-collateral crossing threshold is approximately:
shock < (1 / HF) - 1 = -2.8007%.

The next-lowest sampled HF was approximately 1.0609498463, whose uniform-collateral crossing lies beyond the frozen -5% grid.

## Interpretation allowed

The source-pilot engine can represent a non-linear liquidation-eligibility cliff.

## Interpretation prohibited

Do not infer:
- this is the full Aave liquidation inventory;
- -3% predicts a market move;
- 304k USD is the protocol-wide amount at risk;
- this is an edge, candidate promotion or trading signal.

The borrower sample is bounded and source-selected, not a full protocol census.
