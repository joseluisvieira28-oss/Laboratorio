# MSEL-001 — Pilot25 V14 Closeout V0.1

Status: `PILOT25_PARTIAL_GATES_FAIL`

Governance: research-only / fail-closed / no live trading / no exchange mutation / no main merge / no post-outcome tuning.

## Frozen evaluator authority

- Evaluator commit: `83876bdacdc481f80fa338dd4187fb9575e3209c`
- Entry authority: V12A T+5 deterministic gross 0.01 SOL Pump bonding-curve quote
- Future evidence: observed Pump SELL only, >=0.01 SOL
- Catastrophe: observed sell-side return <= -80% OR complete 24h source coverage with no qualifying SELL
- Winner: observed sell-side return >= +100%
- Stress: fixed 3.00% haircut

## Integrity gate

- 904 / 904 sealed V13 raw transactions hash-verified
- Missing transaction results: 0
- Pump migrate transactions detected: 0
- PumpSwap Buy/Sell/CreatePool event records detected: 0
- Valid qualifying future Pump SELL executions: 242

## Pilot25 frozen results

| Slice | N | Catastrophes | Catastrophe rate | +100% winners |
|---|---:|---:|---:|---:|
| Full | 25 | 16 | 64.00% | 1 |
| Safest 20% | 5 | 2 | 40.00% | 1 |
| Safest 50% | 13 | 9 | 69.23% | 1 |
| Riskiest 20% | 5 | 2 | 40.00% | 0 |

Frozen partial gates:

- Gate 1 — safest20 catastrophe <= 60% baseline: **FAIL**
- Gate 2 — safest50 catastrophe <= 80% baseline: **FAIL**
- Gate 3 — riskiest20 catastrophe >= 1.5x baseline: **FAIL**
- Gate 4 — safest50 winner retention >= 50%: **PASS**
- Gate 5 — structural vs price/volume control: **NOT EVALUATED IN PILOT25**
- Gate 6 — three chronological OOS blocks: **NOT EVALUATED IN PILOT25**
- Gate 7 — leakage/source gate: **PASS**

All 16 catastrophes were classified through the frozen liquidity-absence rule. The single +100% winner reached approximately +220.22% raw maximum observed return and was primary risk rank 2. Catastrophe/winner counts were unchanged by the frozen 3% stress.

## Output hashes

- `pilot25_outcomes_v14.jsonl`: `001941bf5f45b5cbb8ae910e23675a6751fb6d2ae3d2bef40e1d1ae662c6eb83`
- `valid_future_pump_sells_v14.jsonl`: `99c2a8b0f107b92025be7997f55024724e25fb07eb708b935985e9044a8eaa52`
- `pilot25_slice_stats_v14.json`: `7f75a42e4da593e58f9dac5cd9880844de744debd9420158792c1ff189923e65`
- `pilot25_partial_mve_gates_v14.json`: `5d6ea5c4e6481cc2d67252e18d796ab38719c0be93ee4158d16c9fc9d629a9ee`
- `pilot25_outcome_manifest_v14.json`: `3419bb941cc4cafb37ec157d5510339c08711ed5c6de33b94e05f8a5d4f8c0ae`

## Interpretation / hard stop

This is not a full-MVE `NO_EDGE` verdict because the frozen evaluator explicitly leaves Gates 5 and 6 unevaluated and `full_mve_verdict_authorized=false`. It is also not a technical/source failure: integrity passed and labels were computed.

The frozen MSEL-001 hidden-concentration + Organicity pilot ranking did not show the required monotonic catastrophe separation. Three of four evaluable partial economic gates failed; the only passing economic gate depends on one winner.

No rescue is authorized. Do not change slices, thresholds, sell floor, T+5 entry, stress, cohort, or risk score after these outcomes. Any next attack must be a materially different, independently frozen experiment.

Drive human closeout: `MSEL-001 — Pilot25 V14 Economic Evaluation Closeout — 2026-09-16` (`1FdghYBLuVhZXSpmVX7eMoiJrIRLAVZ6TUi_qWH_p8nc`).
Drive evidence ZIP: `MSEL_PILOT25_V14_RESULTS.zip` (`1-jcVg-q3AMCD-vH2N5XekWBr4WwuFkz4`).
