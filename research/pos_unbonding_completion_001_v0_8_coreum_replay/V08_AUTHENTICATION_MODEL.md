# V0.8 Coreum replay authentication model

Candidate: POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001  
Scope: tooling/source qualification only. No census or market outcomes.

This note records how the frozen V0.8 offline replay authenticates Source-A block transport without treating the archive RPC as an independent application-state source.

## Transport vs computation

- Raw block JSON is transported only from the frozen V0.7/V0.8 archive endpoint.
- No remote `block_results` are consumed.
- The exact historical Coreum application revision executes InitChain and every block locally.
- Local ABCI BeginBlock / DeliverTx / EndBlock / Commit results produce the application state and AppHash.

## Consensus authentication inside the native executor

The pinned Tendermint 0.34 BlockExecutor `ApplyBlock` calls `validateBlock` before application execution. That validation checks, against locally evolved consensus state:

- chain-id and exact next height;
- predecessor BlockID;
- prior AppHash and LastResultsHash;
- ConsensusHash;
- ValidatorsHash and NextValidatorsHash;
- the previous height's LastCommit signatures using the locally stored LastValidators set;
- proposer membership and canonical block time.

The typed importer additionally recomputes the block hash from the decoded block and requires equality with the reported BlockID hash. `Block.ValidateBasic`, reached by `validateBlock`, validates internal block consistency including data/evidence/header commitments.

Therefore archive transport is not accepted merely because the RPC returned JSON: each sequential block must be compatible with the locally reconstructed consensus/application prefix and its signed validator history.

## Evidence

Canonical evidence embedded in an authenticated block is forwarded by the native execution path into ABCI BeginBlock as ByzantineValidators exactly as Tendermint replay does. The chunk executor records evidence counts; it does not silently skip evidence-bearing blocks.

## Checkpoints

A resumable checkpoint is valid only when:

1. every preceding block in the prefix passed native validation and local ABCI execution;
2. local post-H AppHash equals header H+1 AppHash;
3. the checkpoint manifest hashes every persisted app/state DB and home file;
4. source revision, genesis hash, height, final AppHash and parent-checkpoint hash are pinned;
5. the next chunk reopens those exact DB bytes and begins at H+1.

This does not claim independent transport and does not by itself pass G2. It is the frozen independent-computation/reconstruction route described by V0.7/V0.8.
