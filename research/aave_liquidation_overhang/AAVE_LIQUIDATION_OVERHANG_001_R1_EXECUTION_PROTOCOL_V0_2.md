# AAVE-LIQUIDATION-OVERHANG-001 — R1 EXECUTION PROTOCOL V0.2

Status: **FROZEN BEFORE FIRST R1 RECONSTRUCTION RESULT**  
Date: **2026-09-17**  
Branch: `aave-liquidation-overhang-v0.1`
Supersedes only the underspecified audit-selection/math details of R1 V0.1; scientific scope and firewall are unchanged.

## 1. Authority and frozen envelope

Precondition: `RECONSTRUCTION_R0_PREFLIGHT_PASS_CORRECTED`.

Exact source envelope inherited from canonical R0:
- Ethereum mainnet
- from block `16,490,000`
- through block `21,525,890` inclusive
- 37 point-in-time reserves from the R0 bootstrap receipt

Canonical contracts:
- Pool `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`
- PoolConfigurator `0x64b761D848206f447Fe2dd461b0c635Ec39EbB27`
- PoolAddressesProvider `0x2f39d218133AFaB8F2B819B1066c7E434Ad94E9e`
- activation oracle `0x54586bE62E3c3580375aE3723C145253060Ca0C2`

Protected-period access beyond the frozen endpoint is forbidden.

## 2. Exact token-native scaled-ledger rules

Use the Aave V3 round-half-up ray arithmetic:
- `RAY = 10**27`
- `rayMul(a,b) = (a*b + RAY//2)//RAY`
- `rayDiv(a,b) = (a*RAY + b//2)//b`

For `IScaledBalanceToken.Mint(caller,onBehalfOf,value,balanceIncrease,index)`:
- if `value > balanceIncrease`: `delta = +rayDiv(value-balanceIncrease,index)`;
- if `value == balanceIncrease`: `delta = 0`;
- if `value < balanceIncrease`: documented burn-path Mint; `delta = -rayDiv(balanceIncrease-value,index)`.

For `IScaledBalanceToken.Burn(from,target,value,balanceIncrease,index)`:
- `delta = -rayDiv(value+balanceIncrease,index)`.

For aToken `BalanceTransfer(from,to,value,index)`:
- `value` is already scaled;
- debit `from` by `value` and credit `to` by `value` exactly.

Variable-debt tokens are non-transferable. An aToken-style `BalanceTransfer` emitted by a variable-debt token is a provenance/reconciliation failure.

These token-native events are the primary scaled-balance ledger. Pool Supply/Withdraw/Borrow/Repay/Liquidation remain independent reconciliation surfaces and may not replace missing token history.

## 3. Prospectively frozen validation sample

Borrower universe:
1. collect every unique `Borrow.onBehalfOf` address in the frozen source envelope;
2. compute `keccak256(raw 20-byte borrower address)`;
3. sort ascending by `(digest,address)`;
4. select exactly the first **16** borrowers.

The sample is outcome-blind and may not be changed after the first R1 audit output is inspected.

Fixed audit blocks, derived only from the frozen block envelope:
- 25% block: `17,748,972`
- 50% block: `19,007,945`
- 75% block: `20,266,917`
- end block: `21,525,890`

For every selected borrower/token pair that has been touched at or before an audit block, the replayed scaled balance at that block is a validation target. A touched pair that has returned to zero remains a validation target.

## 4. Independent historical-state rule

Validate each target with historical `scaledBalanceOf(address)` via independent Ethereum archive RPCs at the exact audit block.

Candidate public endpoints are fixed before the run:
- `https://ethereum-rpc.publicnode.com`
- `https://eth.drpc.org`
- `https://1rpc.io/eth`
- `https://eth.llamarpc.com`
- `https://rpc.ankr.com/eth`

Per target:
- at least 2 endpoints must return a usable historical value;
- all usable values must agree exactly;
- replayed value must equal the agreed value exactly.

Adjudication:
- fewer than 2 usable endpoints for any required target => `RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE`;
- independent endpoints disagree => `RECONSTRUCTION_PROVENANCE_FAILURE`;
- replay differs from agreed historical state => `RECONSTRUCTION_RECONCILIATION_FAILURE`.

No failed target may be removed or replaced after inspection.

## 5. Transport and ordering

SQD endpoint: `https://portal.sqd.dev/datasets/ethereum-mainnet/stream`.

Use the empirically validated continuation rule:
`cursor = max(blockNumber returned by page) + 1`.

`toBlock` is inclusive. Every canonical log identity `(transactionHash,logIndex)` must be unique within a query family. Records outside the frozen envelope fail closed.

Replay order is `(blockNumber, transactionIndex, logIndex)` when transactionIndex is provided. If a query lacks transactionIndex, provider order within block/transaction is retained and any ambiguity capable of changing state fails closed.

## 6. Audit PASS and full-R1 authorization

The deterministic audit may emit only:
- `R1_AUDIT_PASS`
- `RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE`
- `RECONSTRUCTION_PROVENANCE_FAILURE`
- `RECONSTRUCTION_RECONCILIATION_FAILURE`
- `RECONSTRUCTION_INSUFFICIENT_COVERAGE`

Only `R1_AUDIT_PASS` authorizes the full 37-reserve R1 replay.

Full R1 still must satisfy all ten mandatory tests in the parent Reconstruction Gate Authority V0.1 before `RECONSTRUCTION_DATA_PASS` can be emitted.

## 7. Unchanged firewall

R1 must not compute or inspect:
- health factor;
- liquidation-overhang predictor;
- adverse-shock threshold;
- future liquidation outcome;
- market returns;
- PnL, PF, win rate or drawdown;
- 2025/2026 data.

No live trading, exchange mutation, wallet use, order creation, alerts/webhooks or merge to main is authorized.
