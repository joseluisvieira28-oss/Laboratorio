# AAVE-LIQUIDATION-OVERHANG-001 — R1 CONTINUATION ORCHESTRATION FREEZE V0.1

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE ORCHESTRATION EXECUTION / OUTCOME-BLIND**

## Purpose

Continue the already-frozen R1 borrower-state reconstruction immediately after the wall-clock-remediated deterministic audit, without changing any scientific rule.

## Exact upstream authority

The only admissible audit source for this orchestration is GitHub Actions run:

- run id: `35355395431`
- workflow: `AAVE Liquidation Overhang 001 — R1 Scaled Ledger Audit V0.1`
- head at launch: `3c72e36e1f7681f2a50c16a0dc06ddd1f59fba22`
- expected artifact: `AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_1`
- required receipt classification: **R1_AUDIT_PASS**

No other run may be substituted. A missing artifact, non-successful workflow conclusion, unreadable receipt, or any classification other than `R1_AUDIT_PASS` closes the continuation fail-closed.

## Downstream components already frozen/prepared

Only after the exact audit passes:

1. Run the prepared global state/oracle gate:
   `research/aave_liquidation_overhang/r1_global_state_v01.py`
2. Run exactly eight reserve replay shards:
   `research/aave_liquidation_overhang/r1_reserve_shard_v02.py`
   with `R1_SHARD_COUNT=8` and shard ids `0..7`.
3. Aggregate with:
   `research/aave_liquidation_overhang/aggregate_r1_reconstruction_v02.py`.

Canonical R0 bootstrap remains pinned to the already-used artifact from run `35218275356` and classification `RECONSTRUCTION_R0_BOOTSTRAP_PASS`.

## No scientific changes

This orchestration does not alter:

- reserve universe;
- sample users;
- audit blocks;
- historical envelope;
- event semantics;
- ray arithmetic;
- token ledger rules;
- eMode/configuration/oracle rules;
- independent RPC quorum;
- pass/fail thresholds;
- predictor definition;
- outcome horizon;
- any market/trading assumption.

It changes only execution ordering and parallelization of already-prepared source-reconstruction components.

## Fail-closed terminal rule

Only the canonical aggregate may emit `RECONSTRUCTION_DATA_PASS`.

Any component failure is preserved under its original terminal failure class. No failed shard/target/user/reserve may be dropped, replaced or retried with altered scientific rules.

## Safety

Still forbidden throughout this orchestration:

- health factor;
- liquidation-overhang predictor;
- adverse-shock threshold;
- future liquidation outcome;
- market-return prices;
- returns/PnL/PF/win-rate/drawdown;
- 2025/2026 access;
- live trading, orders, wallets, exchange mutation, alerts/webhooks;
- merge to main.

A `RECONSTRUCTION_DATA_PASS` authorizes only the separately frozen creation of a FINAL PRE-DISCOVERY protocol. It does not authorize Discovery by itself.
