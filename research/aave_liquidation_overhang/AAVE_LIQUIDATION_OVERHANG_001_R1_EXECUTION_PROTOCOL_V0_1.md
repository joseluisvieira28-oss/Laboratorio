# AAVE-LIQUIDATION-OVERHANG-001 — R1 FULL STATE RECONSTRUCTION EXECUTION PROTOCOL V0.1

Status: FROZEN / AUTHORIZED
Date: 2026-09-17
Branch: `aave-liquidation-overhang-v0.1`
Precondition: `RECONSTRUCTION_R0_PREFLIGHT_PASS_CORRECTED`
Next terminal classifications are limited to the classifications in the frozen Reconstruction Gate Authority V0.1.

## Purpose
Reconstruct borrower-level Aave V3 Ethereum historical state through 2024-12-31 without current-state substitution, survivorship leakage, protected-period access, predictor construction, future outcomes, returns or PnL.

## Frozen primary ledger semantics
1. aToken scaled collateral ledger is token-native.
   - `BalanceTransfer(from,to,value,index)`: `value` is the scaled quantity; debit `from`, credit `to` by exactly `value`.
   - Mint/Burn must be decoded using the contemporaneous scaled-token semantics and must account for the documented case in which a burn transaction can emit Mint because accrued interest exceeds the requested burn.
   - Pool Supply/Withdraw/Liquidation are reconciliation surfaces, not the primary scaled-balance ledger.
2. Variable debt ledger is token-native and non-transferable.
   - Reconstruct scaled debt from version-correct variable-debt Mint/Burn events.
   - Pool Borrow/Repay/Liquidation is an independent reconciliation route.
   - Any stable-rate Borrow observation is fail-closed review; R0 observed only rate mode 2.
3. Reserve indices are point-in-time.
   - Initialize liquidityIndex and variableBorrowIndex at RAY on reserve initialization.
   - Replay ReserveDataUpdated in strict chain order.
   - For snapshot timestamps between state updates, normalized income/debt must use the implementation-compatible Aave linear/compounded-interest formulas and exact ray arithmetic/rounding.
4. User state includes collateral-enabled flags and eMode category from time-ordered Pool events only.
5. Reserve configuration includes reserve identity, decimals, activity and historical collateral/eMode parameters from point-in-time initialization/configurator history. Current membership/configuration may not be substituted.
6. Oracle mapping remains the point-in-time provider/oracle/source provenance proven in R0; every observation used later must have timestamp <= snapshot timestamp.

## Ordering
Canonical event key: `(blockNumber, transactionIndex, logIndex)` where transactionIndex is available; otherwise preserve provider-returned canonical transaction/log ordering and fail closed on ambiguous same-block dependencies. No state transition may be reordered for convenience.

## Sharding
Acquisition may be sharded by reserve and bounded block interval. Every shard must record: chain, frozen start/end block, reserve, token identities, query family, first/last observed block, event count, retries, and content digest. Shards are merged only by canonical event key.

## Mandatory R1 gates
All ten frozen authority tests remain mandatory:
1. reserve identity;
2. source coverage;
3. scaled collateral conservation;
4. scaled debt conservation/non-transferability;
5. collateral flags;
6. eMode;
7. reserve indices;
8. oracle provenance;
9. prospectively selected independent historical validation sample;
10. protected-period firewall.

## Deterministic validation sample
Before reconstruction results are inspected, select validation blocks/users deterministically from source identities/block envelope (hash-based selection; no liquidation/return/outcome input). Compare reconstructed account ingredients to legitimate historical state queries or an independent canonical representation. Failure to obtain an independent route is not silently waived.

## Fail-closed invariants
- materially negative scaled balance/debt => reconciliation failure;
- unexplained token identity/configuration discontinuity => provenance failure;
- missing active interval => insufficient coverage;
- unsupported implementation semantic boundary => provenance failure;
- stable-rate borrow => fail-closed review;
- any 2025/2026 source access => firewall violation and invalid run;
- any predictor/HF-overhang/outcome/return/PnL computation => invalid run.

## Explicitly forbidden in R1
No liquidation-overhang predictor, no adverse-shock threshold, no future liquidation outcome, no market returns, no PnL, no PF/win-rate/drawdown, no 2025/2026, no exchange/wallet/order/alert/webhook activity, no merge to main, no live trading.

## Exit
Only a fully reconciled R1 may emit `RECONSTRUCTION_DATA_PASS`. A pass authorizes only creation of the separately frozen FINAL_PRE_DISCOVERY_PROTOCOL; it does not authorize Discovery automatically.