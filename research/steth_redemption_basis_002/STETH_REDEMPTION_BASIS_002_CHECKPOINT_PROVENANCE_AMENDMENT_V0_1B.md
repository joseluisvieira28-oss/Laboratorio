# STETH-REDEMPTION-BASIS-002 — CHECKPOINT PROVENANCE AMENDMENT V0.1B

Status: **FROZEN BEFORE DISCOVERY OUTCOMES**
Date: **2026-09-18**

This amendment supersedes only section 7 of DISCOVERY IMPLEMENTATION SEMANTICS FREEZE V0.1.

Reason: a WithdrawalQueue finalization can be emitted by an internal call during a larger Accounting/Lido transaction. The top-level Ethereum transaction calldata is therefore not a guaranteed direct encoding of WithdrawalQueue `finalize(uint256,uint256)`.

No economic outcome was opened before this correction.

## Canonical checkpoint reconstruction

WithdrawalQueueBase freezes:

`CHECKPOINTS_POSITION = keccak256("lido.WithdrawalQueue.checkpoints")`

Each successful finalization creates exactly one new checkpoint:

`Checkpoint(firstRequestIdToFinalize, maxShareRate)`

and then emits:

`WithdrawalsFinalized(firstRequestIdToFinalize, lastRequestIdToBeFinalized, ...)`

The exact V0.1B method is:

1. read `getLastCheckpointIndex()` at block `17,272,127`, immediately before the first frozen Discovery block;
2. acquire every canonical `WithdrawalsFinalized` log from block `17,272,128` through block `21,522,315`, ordered by block number, transaction index/log index;
3. checkpoint index for event ordinal `j` (1-based) is:
   `initial_checkpoint_index + j`;
4. mapping storage location is:
   `keccak256(abi.encode(checkpoint_index, CHECKPOINTS_POSITION))`;
5. first struct slot must equal the event's indexed `from` request id;
6. second struct slot is the exact `maxShareRate`;
7. exact storage values require 2-of-3 archive-provider quorum at the event block;
8. at final block `21,522,315`, `getLastCheckpointIndex()` must equal:
   `initial_checkpoint_index + number_of_frozen_period_finalization_events`.

Any failure of these invariants is `DISCOVERY_TECHNICAL_OR_PROVENANCE_FAILURE`.

No trace API, inferred share rate, averaged value, actual-request claim amount, fitted value or transaction-calldata guess may replace this storage-bound checkpoint.

The protocol-exact hypothetical claim formula in section 8 of the implementation freeze remains unchanged.
