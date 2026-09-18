# AAVE-LIQUIDATION-OVERHANG-001 — R1 CONTINUATION ORCHESTRATION FREEZE V0.2

Date: 2026-09-18
Branch: `aave-liquidation-overhang-v0.1`
Status: **FROZEN BEFORE V0.2 AUDIT RESULT / OUTCOME-BLIND**

## Admissible upstream audit

The only admissible upstream audit is the **first GitHub Actions run** of:
- workflow: `AAVE Liquidation Overhang 001 — R1 Scaled Ledger Audit V0.1`
- branch: `aave-liquidation-overhang-v0.1`
- triggered by the timeout-only V0.2 workflow change authorized by
  `AAVE_LIQUIDATION_OVERHANG_001_R1_WALL_CLOCK_REMEDIATION_V0_2.md`.

It must:
- complete successfully;
- emit artifact `AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_1`;
- emit classification exactly `R1_AUDIT_PASS`;
- preserve all frozen R1 semantics.

If the first run fails, cancels, produces no artifact, or emits any other classification, V0.2 continuation closes fail-closed.

## Downstream sequence if and only if the audit passes

1. exact global state/oracle gate;
2. exactly eight reserve replay shards with ids 0..7;
3. exact canonical aggregate.

Only the aggregate may emit `RECONSTRUCTION_DATA_PASS`.

No failed shard/reserve/user/target may be dropped or substituted.

## Safety

Still forbidden:
- health factor;
- liquidation-overhang predictor;
- adverse-shock threshold;
- future liquidation outcomes;
- market-return prices;
- returns/PnL/PF/win-rate/drawdown;
- 2025/2026;
- live trading/orders/wallets/exchange mutation;
- main merge.

A reconstruction PASS may authorize only the separately frozen next pre-Discovery stage; it does not authorize Discovery automatically.
