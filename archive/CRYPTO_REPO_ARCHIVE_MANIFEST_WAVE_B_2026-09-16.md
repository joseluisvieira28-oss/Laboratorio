# CRYPTO REPO ARCHIVE MANIFEST — WAVE B — 2026-09-16

Purpose: preserve additional closed / superseded Crypto Lab branch histories identified during the branch-by-branch HOLD adjudication.

Governance:
- archive-only evidence preservation
- no scientific verdict rewriting
- no live trading
- no exchange mutation
- no protected holdout opening
- no strategy rescue
- no merge to main
- BLOCKED / DATA_FAILURE / SOURCE_FAILURE / INSUFFICIENT_SAMPLE / ACTIVE / WATCHLIST lines excluded
- original branch refs are not deleted by this action

Archive ref: `archive/crypto-closed-labs-2026-09-16`
Prior archive vault: `f1573a4081574a6e34ef2518c74242e0a4ad7207`
Wave B: 10 branch refs.

## Wave B — SAFE_TO_ARCHIVE = YES

| Branch | Frozen HEAD | Final basis for archive |
|---|---|---|
| `bnb-launchpool-demand-v0.1` | `46104f6057701abf6b7c6330263f94f0557fcb42` | `DISCOVERY_FAIL_NO_PROMOTION`; one-shot Discovery sealed; no rerun/rescue. |
| `capitulation-reversion-v0.1` | `d2a1808a992efc74f95f7d6a3a187ec666c54f5e` | Closed; partial replication/not-fresh-information family; no rescue of prior mean-reversion family. |
| `etf-shortflow-v0.1` | `0b086438cc62e33518139e82d282a8446f431a0f` | `DISCOVERY_FAIL_NO_PROMOTION`; negative gross/net economics; explicitly not a near-miss. |
| `htf-donchian-shadow-v0.1` | `11b19990579adc4175dcb85bd52767d991492ec4` | `SHADOW_READINESS_FAIL`; 6H production path closed. |
| `ops-dispatch-options-20260913` | `bde7f3978a4a2bacbce1b45e438c6dc6e6fb54d7` | Superseded technical dispatch for OPTIONS-SPOTPERP-002; exact candidate subsequently closed `TIER4_REJECTED / OOS_FAILED`. |
| `options-expiry-reversal-v0.1` | `5583b0beb9b9108e203556804eebe502a558fad4` | `NO_STATISTICAL_EDGE`; failed and closed; no rescue. |
| `perpetual-launch-shock-v0.1-source-gate` | `d4da7fde197c6d331dc840831ec25a9e426d3be0` | Final `NO_CAUSAL_LAUNCH_INTENSITY_EDGE`; exact mechanism closed, no rescue. |
| `perpetual-launch-shock-v0.1` | `5142553275e63724cfad8a9b138a4636be2f093a` | Stale/base ref pointing at existing main commit; canonical PLS evidence is on the source-gate/closeout lineage. This HEAD is already reachable from the prior archive vault. |
| `stablecoin-exchange-flow-v0.1` | `e669cbde18ca810fa5a341bef27fe34f42d0af44` | `NO_STATISTICAL_EDGE / NEGATIVE_EXPECTANCY`; exact MVE closed. |
| `treasury-auction-demand-v0.1` | `7f8dbf1458fd7bc0b9fba9aa23bccd1170dfc108` | `DISCOVERY_FAIL_NO_PROMOTION`; net economics and robustness gates failed; exact MVE closed. |

## Explicitly protected findings from HOLD audit

The following are intentionally NOT archived by Wave B:

- `tf-gap-donchian-1d-v0.1`: `INSUFFICIENT_SAMPLE`, 98 resolved vs frozen minimum 100; BASE expectancy about +0.663R, PF about 2.29, bootstrap lower 95% about +0.281R, STRESS expectancy about +0.639R. No two-trade rescue is allowed; any continuation must be a new independent prospective replication.
- `btc-options-expiry-reversal-v2-path2-2024-v01`: `TIER_3_WATCHLIST_WEAK_CANDIDATE`; positive base-cost economics but failed stress and leave-one-out stability; 2025/2026 rescue prohibited.
- `btc-options-expiry-reversal-v0.1`: parent authority/lineage retained because the V2 Path 2 child remains a Tier-3 watchlist line.
- `btc-dvol-futures-termstructure-v0.1`: `SOURCE_DATA_INSUFFICIENT_OR_BLOCKED`, explicitly not NO_EDGE.
- `btc-options-vrp-*`: active/source-remediation/paused-not-failed states.
- `etf-creation-flow-v0.1`: `SOURCE_FEASIBILITY_BLOCKED`, not NO_EDGE.
- `exchange-delisting-shock-v0.1` plus source-remediation refs: canonical `INSUFFICIENT_SOURCE_SAMPLE`; no market verdict.
- `htf-dh02-validation-v0.1`: branch terminates at a pre-outcome validation freeze; no same-ref final authority sufficient for pruning.
- `mve-hunt-action-pack-v0.1`: contains active protected CPI validation authority.
- `options-expiry-gamma-v0.1`: `SOURCE_ACCESS_BLOCKED / SOURCE_ENGINEERING_NOT_PROVEN`, not market-negative.
- `quarterly-basis-convergence-v0.1`: `DATA_FAILURE`, not NO_EDGE.
- `stablecoin-peg-dislocation-v0.1`: active Discovery workflow.
- `tf-gap-pbr01-1d-v0.1`: `INSUFFICIENT_SAMPLE` with positive descriptive point estimates.
- `tf-gap-pbr01-4h-v0.1`: corpus/source recovery still active.
- `whale-cex-netflow-v0.1`: active source gate; outcomes and protected periods remain locked.

## Reachability policy

This manifest is committed on top of the Wave A archive vault. The Wave B vault commit makes each unique Wave B HEAD that is not already reachable from Wave A an additional Git parent. Therefore the historical commits remain reachable from the single archive ref without merging into `main` or rewriting any branch history.
