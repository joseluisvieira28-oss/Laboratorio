# BNB-LAUNCHPOOL-DEMAND-001 — RED TEAM REPORT V0.1

**Attack plan freeze commit:** `705e53aa0ba4584e8987c451064e64d132cbbe17`  
**Red verdict:** **CHALLENGED — NOT FALSIFIED / MANDATORY ATTACKS STILL BLOCKED BY MISSING RAW CONTROL INPUTS**

The attack plan was persisted before the Blue conclusion report.

## Executed attacks

| Attack | Result | Finding |
|---|---|---|
| RT-001 LOOKAHEAD | PASS | Historical runners enforce protected-year guards and consume the frozen signal timestamp plus required entry/exit opens. |
| RT-002 TIMESTAMP_PROVENANCE | PASS | Canonical Binance publication timestamp is the event clock; entry is strictly after signal time; source manifests/hashes are preserved. |
| RT-003 LEAKAGE | PASS | Discovery runner explicitly forbids high/low/close/volume and parses open only at the frozen entry/exit timestamps. |
| RT-004 RANDOM_SIGNAL_PLACEBO | BLOCKED | Current audit has immutable ledgers/results but not the full canonical raw market archives in the review branch/runtime needed for a defensible randomized event-time control. |
| RT-005 TIME_SHIFT_PLACEBO | BLOCKED | Same raw-history limitation. No synthetic substitute is allowed. |
| RT-006 ASSET_PLACEBO | BLOCKED | A matched historical control universe was not frozen for this candidate; inventing one now risks post-outcome selection. |
| RT-007 PARAMETER_PERTURBATION | BLOCKED | Requires canonical raw history. Results may only be diagnostic and cannot rescue/change this exact candidate. |
| RT-008 COST_STRESS_X2 | PASS | Repriced at 40 bps RT: pooled mean +60.1639 bps, PF 1.4686. All 3 blocks remain positive with PF>1. |
| RT-009 COST_STRESS_X3 | PASS | Repriced at 60 bps RT: pooled mean +40.1639 bps, PF 1.2901. All 3 blocks remain positive with PF>1. |
| RT-010 SLIPPAGE_CAPACITY | CHALLENGE | Historical fixed-cost envelope does not prove executable depth/capacity for capital. |
| RT-011 REGIME_SPLIT | CHALLENGE | 2020: -89.1787 bps/trade, PF 0.5991; 2021: +213.0542, PF 2.0689. Strong temporal dependence exists. |
| RT-012 PERIOD_STABILITY | CHALLENGE | All 3 aggregate blocks are positive, but effect magnitude and concentration vary materially; two blocks breach old within-block concentration limits. |
| RT-013 REMOVE_BEST_1 | PASS | Remove largest winner: N=65, mean +26.9877 bps, PF 1.2230. Edge does not depend on one trade alone. |
| RT-014 REMOVE_BEST_5 | CHALLENGE | Remove five largest winners: N=61, mean -17.0460 bps, PF 0.8678. Historical economics depend materially on a small winner tail. |
| RT-015 BLOCK_BOOTSTRAP | CHALLENGE | Discovery CI lower bound -11.19 bps; 2025 OOS -54.14; pre-Discovery -202.71. Uncertainty remains large. |
| RT-016 BETA_OR_COMMON_FACTOR | PASS WITH LIMITATION | Primary return is BNBBTC, already relative to BTC, reducing simple broad-BTC-direction explanation; no broader factor decomposition is claimed. |
| RT-017 VOLATILITY_EXPLANATION | BLOCKED | No pre-frozen volatility-matched control is available in the current immutable review inputs. |
| RT-018 MULTIPLE_TESTING | CHALLENGE | Candidate-specific mechanism/source freezes are recoverable, but a complete global multiplicity ledger for every idea that preceded BNB is not proven by this review. |
| RT-019 EXECUTION_REALISM | CHALLENGE | Exact timestamp/execution semantics and fixed costs are strong; historical executable depth/slippage/capacity evidence is incomplete. |
| RT-020 FORWARD_CONTRADICTION | NOT_APPLICABLE | Diamond V0.2 forbids an early final verdict before the first 25 complete prospective matched events. |
| RT-021 SOURCE_ALTERNATIVE | BLOCKED | Optional; no second canonical announcement source can replace Binance authority. |
| RT-022 EVENT_CLUSTER | PASS | <=60m clustering, one-active-trade and overlap suppression are explicit in freeze/runner lineage. |
| RT-023 DOMINANT_SUBGROUP | CHALLENGE | 2021 dominates the old presample and the top-five pooled winners are economically decisive. No subgroup filter is authorized. |
| RT-024 BOUNDARY_ATTACK | PASS | Forward boundary is commit-timestamp based (2026-09-16T20:51:23Z), no pre-boundary backfill; first-25 causal measurements immutable; sidecar cannot create parent events. |

## Quantitative attack receipt

Pooled immutable historical ledger:

- N = 66
- BASE20 mean = +80.1639378203 bps/trade
- BASE20 PF = 1.6726618887
- remove best 1: +26.9877499571 bps/trade, PF 1.2230251698
- remove best 5: -17.0459589100 bps/trade, PF 0.8678019295
- 40 bps RT: +60.1639378203 bps/trade, PF 1.4685505783
- 60 bps RT: +40.1639378203 bps/trade, PF 1.2900902668

### Severe-cost block check at 60 bps RT

- Discovery: +48.8665 bps/trade, PF 1.5179
- 2025 OOS: +17.6174 bps/trade, PF 1.3159
- Pre-Discovery: +36.8526 bps/trade, PF 1.1725

## Red conclusion

The current evidence does **not** falsify the exact BNB candidate. It survives single-winner removal and unusually harsh static cost stress.

However, the five-winner removal failure, temporal dependence, negative bootstrap lower bounds and incomplete execution/control-placebo evidence are material. Red therefore returns **CHALLENGED**, not SURVIVES and not FALSIFIED.

No rule change, filter, threshold, event deletion or historical rescue is authorized from these diagnostics.
