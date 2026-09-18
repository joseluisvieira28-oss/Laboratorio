# AAVE-LIQUIDATION-OVERHANG-001 — R1 COLLATERAL FLAG SEMANTICS AMENDMENT V0.1

Date: 2026-09-18
Status: FROZEN BEFORE REMEDIATED SHARD REPLAY
Scope: reconstruction-only / outcome-blind

## Trigger evidence

R1 V0.3 reserve shards reported only this collateral diagnostic:
collateral_flag_true_with_zero_scaled_atoken_at_tx_end

A prospectively frozen source-only state probe then queried five exact violation pairs at block 21,525,890 using the frozen three-provider archive set and quorum=2.

Probe run: 35384176433
Artifact: 10563825131
Artifact digest: sha256:14714b00d328f7f9b946b564b5836a2b2c31b9de7a054aed9ce34393bc0b3429
Classification: STALE_COLLATERAL_FLAG_ZERO_SCALED_STATE_OBSERVED

Observed canonical protocol state:
3 of 5 frozen pairs had scaledBalanceOf(user)=0 while the Aave user-configuration collateral bit remained true.

No health factor, overhang, future liquidation outcome, market price, return or PnL was opened.

## Protocol semantics

Aave V3 disables collateral on standard transfer when balanceFromBefore == amount in underlying units, while aToken ledger movement is amount.rayDiv(index) in scaled units. Exact underlying equality is therefore not equivalent to the condition scaledBalanceAfter == 0 under ray rounding.

The protocol can legitimately retain a collateral bit while the scaled aToken balance is zero.

Therefore the invariant:
collateral flag true => scaled aToken balance > 0
is invalid and MUST NOT be a reconstruction-failure criterion.

## Exact remediation

Only the following diagnostic is demoted from terminal reconciliation failure to non-terminal protocol-semantic diagnostic:
collateral_flag_true_with_zero_scaled_atoken_at_tx_end

The count and exact rows MUST remain in the receipt.

Still terminal / unchanged:
- negative scaled balances;
- reserve index decreases;
- variable-debt BalanceTransfer;
- missing deterministic reserve coverage;
- malformed/duplicate provenance;
- any other reconciliation violation;
- any shard envelope or reserve-union mismatch.

No ledger delta formula changes.
No event source changes.
No reserve universe changes.
No block-window changes.
No sample changes.
No oracle changes.
No health factor or overhang.
No outcomes.
No 2025/2026.
No live trading.
No exchange mutation.
No main merge.
