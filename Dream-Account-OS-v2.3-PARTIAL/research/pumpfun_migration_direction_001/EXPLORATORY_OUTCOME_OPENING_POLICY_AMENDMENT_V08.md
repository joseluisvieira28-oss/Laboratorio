# PMD-001 — EXPLORATORY OUTCOME OPENING POLICY AMENDMENT V0.8

Date: 2026-09-16
Branch: `pumpfun-migration-direction-v0.1`
Status: **USER-AUTHORIZED / EXPLORATORY / OUTCOMES MAY OPEN / NO PROMOTION AUTHORITY**

## 1. Purpose

The operator explicitly authorizes opening post-migration direction, returns and counterfactual unit-notional PnL before completion of the original confirmatory Source Gate / feature-formula / chronological-partition sequence.

This is a governance change about when outcome values may be inspected. It does **not** rewrite prior source results, change the economic thesis, lower execution costs, replace candidates, or retroactively declare a failed gate to have passed.

## 2. Prior scientific record remains intact

The following remain true and must not be overwritten:

- `CHAIN_EXACT_CROSSDATE_V06_FAIL` remains the V0.6 source-gate result.
- V0.7/V0.7.1 parser/source remediation remains a separate pre-outcome scientific path and may continue unchanged.
- the V0.7 offline re-adjudication result `V07_OFFLINE_BOUNDARY_COVERAGE_20_OF_20` established parser coverage only; it did not itself grant source-gate authority.
- no previous result is re-labelled as PASS merely because outcomes are now permitted to be inspected.

## 3. What V0.8 may open

V0.8 may read actual `price_native` values from the exact canonical PumpSwap pool and calculate:

- 5-minute gross return;
- 5-minute net return after the already-frozen 3.00 percentage-point round-trip stress;
- raw future direction (`UP`, `DOWN`, `FLAT`);
- after-cost economic sign (`NET_POSITIVE`, `NET_NONPOSITIVE`);
- isolated counterfactual PnL assuming 1 SOL notional per observation (`1 SOL * net_return`).

The PnL statistic is an isolated unit-notional diagnostic, **not** a portfolio backtest. Overlapping trades, capital constraints and portfolio scheduling are not modeled.

## 4. Two descriptive populations

### A. Chain-exact Cross-Date 20

Use exactly the 20 frozen Cross-Date candidates already adjudicated by V0.7. For each candidate the causal migration boundary is the unique V0.7 chain-exact `T*` (`migrate` or `migrate_v2` + canonical PumpSwap `CreatePool`).

Outcome execution is re-anchored to the causal boundary:

- entry = first valid exact-canonical-pool price in `[T* + 15s, T* + 90s]`;
- exit target = `entry + 300s`;
- exit = first valid exact-canonical-pool price in `[target, target + 120s]`;
- gross return = `exit / entry - 1`;
- net return = `gross return - 0.03`.

No candidate may be replaced because its outcome is missing or unattractive.

### B. Frozen T0 source-executable baseline

For context only, reconstruct the already-defined clean pre-feature population from the published corpus using the source-resolution rules frozen before outcomes:

- real canonical pool;
- non-Mayhem;
- exclude 2026-07-03;
- entry first valid exact-pool observation in `[corpus_T0 + 15s, corpus_T0 + 90s]`;
- exit first valid exact-pool observation from `entry + 300s` through `entry + 420s`.

This population is descriptive because most rows do not yet have a chain-exact `T*` reconstruction.

## 5. Scientific consequence of opening outcomes early

The same 2026 corpus is no longer eligible to serve as an untouched protected holdout for feature formulas chosen or modified **after** V0.8 outcome inspection.

Therefore:

- V0.8 cannot promote PMD-001 to edge, almost-diamond, shadow or production;
- no feature threshold selected after seeing V0.8 may be called pre-outcome on this corpus;
- no score, feature formula or slice may be tuned to rescue V0.8 results and then validated on the same opened observations as if independent;
- a later confirmatory claim requires a separately frozen unseen replication dataset or a demonstrably precommitted formula evaluated on data not exposed by V0.8.

This contamination rule is the price of opening outcomes early and is mandatory.

## 6. What does not change

The following remain fixed for any economic diagnostic in this lab unless a separately documented future experiment is created:

- demand-absorption-versus-latent-supply thesis;
- canonical PumpSwap pool identity;
- primary 5-minute horizon;
- +15s entry guard;
- +90s entry source cap;
- +120s exit-source tolerance;
- 3.00 percentage-point round-trip execution stress;
- no manual token selection;
- no lower-cost rescue;
- no live trading;
- no exchange mutation;
- no merge to `main`.

## 7. V0.8 verdict vocabulary

V0.8 may report descriptive observations such as positive/negative returns, direction frequencies and unit-notional PnL.

It may **not** emit `EDGE`, `PROMOTED`, `QUASE DIAMANTE`, `DIAMOND`, `SHADOW_PASS` or equivalent promotion labels.

The only authority of V0.8 is exploratory information acquisition.
