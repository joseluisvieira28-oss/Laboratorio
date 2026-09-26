# CRYPTO LAB — DIAMOND TEST V1 — PROSPECTIVE VALIDATION STANDARD

**Policy ID:** `DIAMOND-TEST-V1-FROZEN-2026-09-24`  
**Status:** `FROZEN / PROSPECTIVE / ADDITIVE`  
**Repository:** `joseluisvieira28-oss/Laboratorio`  
**Authority relationship:** additive to `ND-PROMOTION-POLICY-V3.0-FROZEN`; historical V1/V2/V3 verdicts remain immutable.  
**Trading authority:** NONE. This standard cannot create orders, exchange mutation, leverage, wallets, capital deployment, alerts/webhooks, or a merge to `main`.

## 1. Purpose

The Diamond Test answers one question:

> What evidence, defined before protected outcomes are observed, would be strong enough to make us conclude that a candidate is behaving like a real, repeatable market effect rather than a backtest artefact?

The test is deliberately difficult to pass. It is not a new strategy and cannot be used to rescue a failed exact candidate.

## 2. Non-negotiable preregistration

Before any new protected outcome is consumed, the candidate must have an immutable freeze recording:

- exact candidate identity;
- exact signal and direction;
- assets/venues;
- timeframe and holding horizon;
- source authority and point-in-time semantics;
- base and stress costs;
- execution assumptions;
- sample boundary;
- protected OOS/holdout/forward boundary;
- expected mechanism;
- expected sign/payoff shape;
- predeclared regimes or regime-independence claim;
- causal/intermediate observable, when the mechanism implies one;
- primary success metrics;
- falsification metrics;
- minimum sample required for adjudication;
- exact PASS / FAIL / INSUFFICIENT / BLOCKED actions.

No field above may be selected or changed after seeing the protected result.

## 3. Six mandatory evidence gates

A candidate can satisfy Diamond Test V1 only if all applicable gates pass.

### G1 — Net economic reality

- Positive expectancy after frozen realistic base costs.
- PF > 1 at the evidence layer being used.
- Stress costs are reported without fee/cost rescue.
- No result may depend on a retrospective lower-cost assumption.

### G2 — Temporal stability

- The effect must not be explained by one short favourable interval.
- Dense mechanisms require support across predeclared major temporal blocks.
- Rare mechanisms use the already-frozen replicated-block framework.
- A materially negative adequate independent block is a contradiction, not noise to delete.

### G3 — Regime robustness

The candidate must either:

A. survive the predeclared relevant regimes, or  
B. have a regime-dependent mechanism that was frozen before protected outcomes and behaves in the predicted direction.

Post-outcome regime filtering is forbidden.

### G4 — Genuine independent OOS / holdout

The evidence block must be untouched for candidate selection and parameter decisions.

Not independent:
- splitting an optimized sample;
- relabelling previously inspected outcomes;
- selecting the best asset, quarter, cost, horizon, threshold, direction or timeframe after outcomes.

### G5 — Operational realism

The evidence chain must include the relevant real-world constraints:

- source availability;
- timestamp correctness;
- stale-data and duplicate protection;
- realistic fees/spread/slippage;
- minimum notional / capacity limits when applicable;
- latency assumptions when material;
- missing-data behaviour;
- idempotency and restart/redeploy integrity for forward collection;
- fail-closed behaviour on corrupted or incomplete authority.

### G6 — Prospective forward non-degradation

The exact frozen candidate must accumulate genuinely post-freeze evidence.

Forward evidence must be:
- generated without backfill being counted as prospective;
- immutable after signal formation;
- resolved under the same scientific contract;
- compared with the predeclared expectation, not with a moving target.

A good historical result with materially degraded forward economics fails this gate.

## 4. Causal / mechanism fingerprint

Where the proposed mechanism implies an observable intermediate step, that step must be preregistered.

The strongest form of evidence is:

`cause/state -> predicted intermediate observable -> predicted market response -> positive net economics`

A candidate does **not** automatically fail merely because a clean causal mediator cannot be observed. In that case the policy records `CAUSAL_FINGERPRINT_NOT_OBSERVABLE` and the candidate must rely on stronger replication/forward evidence. We do not invent a causal story after seeing PnL.

## 5. Adversarial falsification

Every Diamond freeze must state in advance what would make us say "this is not the thing."

At minimum:

- wrong sign under adequate independent evidence;
- PF <= 1 and non-positive base-net expectancy in an adequate protected block;
- effect disappears under realistic execution;
- effect exists only in a retrospectively selected asset/time/regime;
- forward evidence materially contradicts the historical effect;
- mechanism-implied intermediate observable repeatedly moves the wrong way when it is measurable;
- concentration/tail dependence exceeds a predeclared hard gate when one exists.

A failure is terminal for the exact test. A new hypothesis requires a new candidate identity and new prospective authority.

## 6. Outcome states

Diamond Test V1 uses these states:

- `DIAMOND_TEST_NOT_STARTED`
- `DIAMOND_TEST_ARMED`
- `DIAMOND_TEST_COLLECTING`
- `DIAMOND_TEST_BLOCKED`
- `DIAMOND_TEST_INSUFFICIENT_SAMPLE`
- `DIAMOND_TEST_FAIL`
- `DIAMOND_TEST_SURVIVES`

`DIAMOND_TEST_SURVIVES` is evidence language only. It is not a Tier-1 promotion, not production approval, and not capital authority. Tier adjudication remains governed by Promotion Policy V3 and any later prospectively frozen policy.

## 7. Anti-rescue rules

After protected outcomes are opened, forbidden:

- threshold tuning;
- cost reduction;
- sign inversion;
- asset isolation;
- favourable subperiod selection;
- timeframe substitution;
- event deletion;
- adding a regime filter;
- replacing the source because the result is inconvenient;
- changing the sample minimum;
- redefining the primary metric;
- converting a failed exact test into a "near pass."

Diagnostics may explain failure but cannot change the verdict.

## 8. Current V3 relationship

Promotion Policy V3 remains authoritative for Tier classifications.

Diamond Test V1 is stricter and prospective. Existing Tier-2 / Quase-Diamante status is preserved even when the candidate has not yet passed Diamond Test V1.

The new label answers a different question:

> Has the exact candidate survived a preregistered, adversarial, economically realistic, genuinely prospective validation strong enough to deserve extraordinary confidence?

## 9. Governance

- research-first;
- fail-closed;
- preserve all negative evidence;
- no hidden rescue;
- no protected outcome access without candidate-specific authority;
- no live trading from this document;
- no merge to `main` without separate operator authorization;
- any candidate-specific Diamond freeze must cite this policy ID and its governing V3 authority.
