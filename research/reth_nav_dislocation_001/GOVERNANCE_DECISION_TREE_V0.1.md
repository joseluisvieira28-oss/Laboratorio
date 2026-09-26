# RETH-NAV-DISLOCATION-001 — GOVERNANCE DECISION TREE V0.1

Frozen: 2026-09-26
Scope: exact lab RETH-NAV-DISLOCATION-001.

## Gate 1 — Historical source

Current frozen result:
SOURCE_PASS.

No future failure may be repaired by changing the economic source definition.
Transport-only retries/redundancy are allowed if the exact block-pinned state is preserved.

## Gate 2 — Predictor calibration census

Required:
PREDICTOR_SOURCE_CENSUS_PASS with 556/556 exact frozen blocks.

If BLOCKED after permitted technical retries:
CLOSE exact lab as PREDICTOR_SOURCE_CENSUS_BLOCKED.
Do not reduce coverage, change cadence, drop blocks, switch pool, or impute.

If PASS:
compute only the pre-frozen q05/q95 state calibration.

## Gate 3 — Discovery predictor sample

Required:
DISCOVERY_PREDICTOR_SAMPLE_PASS:
- 139/139 Discovery predictor states valid;
- boundary predecessor valid;
- >=30 transition-entry events total;
- >=10 discount entries;
- >=10 premium entries.

If source blocked:
CLOSE exact lab as DISCOVERY_PREDICTOR_SOURCE_BLOCKED.

If insufficient sample:
CLOSE exact lab as DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE.
Do not widen q05/q95 or change de-clustering to manufacture events.

If PASS:
mechanism Discovery may open exactly as pre-frozen.

## Gate 4 — Mechanism Discovery

Primary:
signed dislocation closure at +7,200 blocks.

PASS requires all frozen statistical conditions.

If FAIL:
CLOSE exact mechanism hypothesis.
Do not invert direction, replace the primary horizon, drop a tail, use +21,600 diagnostic as rescue, or open PnL.

If INSUFFICIENT_SAMPLE:
CLOSE exact Discovery path.

If PASS:
a separate OOS opening receipt may be created.

## Gate 5 — OOS

Region:
25,000,000 <= entry block < 26,000,000.

OOS test design must preserve the exact Discovery state rule, direction and primary mechanism horizon.

No OOS rule tuning is permitted.

If OOS FAIL:
CLOSE exact lab.
Protected holdout remains sealed.

If OOS PASS:
a separate protected-holdout opening authority is required.

## Gate 6 — Protected holdout

Region:
entry block >= 26,000,000.

Holdout remains sealed until explicitly opened by the prior gate and governance.

No holdout tuning.

## Executable economics / PnL

Mechanism PASS, OOS PASS, and even holdout PASS do not automatically authorize a PnL test or live trading.

Before PnL:
- execution route;
- borrow/short feasibility if relevant;
- fee/slippage model;
- notional/capacity;
- entry/exit mechanics

must be frozen separately without observing PnL outcomes.

## Live firewall

No stage in this tree authorizes:
- live orders;
- exchange mutation;
- wallet mutation;
- capital deployment;
- merge to main.

Promotion credit remains zero until governance criteria for edge are explicitly satisfied.
