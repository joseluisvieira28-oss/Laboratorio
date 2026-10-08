# V0.8 DURABLE STORAGE EXTENSION FREEZE

Candidate: POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001  
Date: 2026-10-08  
Parent: COREUM_REPLAY_EXECUTION_FREEZE_V08.md

## Scope

Prospective operational-storage extension only. Scientific rules, G2, Source A identity, materiality, five-chain gate, T_completion and the outcome firewall remain unchanged.

## Raw transport retention

The only Coreum block transport remains:
`https://archive.rpc.mainnet-1.tx.org/block?height=H`

No endpoint substitution and no remote `block_results`.

For every requested height retain: exact URL, UTC request time, HTTP status, attempt/retry history, exact raw bytes, byte count, SHA256, decoded chain-id, decoded height and block hash. Any missing height, terminal HTTP failure, parse failure, identity mismatch or predecessor discontinuity fails closed.

Replay chunks are at most 10,000 applied heights and retain H+1. Lossless packaging must reproduce every raw file byte-for-byte. The manifest hashes every member and the package itself.

## Durable public packages

Exact raw chunks and locally generated replay checkpoints may be retained as GitHub Release assets in this public repository. This is storage of frozen transport bytes and local computation artifacts; it is not a new source or independent provider.

Partition releases by <=1,000,000 heights. Use one raw package per <=10,000-height chunk plus manifests. Uploaded packages are promoted only after size/digest verification against the local receipt.

## Local checkpoints

A resumable state package is admissible only when derived locally from genesis or a prior admissible local checkpoint. Its manifest pins genesis SHA256, Coreum source revision, ending/next height, final AppHash, parent checkpoint SHA256, execution-receipt SHA256 and path/size/SHA256 for every persisted database/home file.

External snapshots or state-sync data remain inadmissible substitutes for the genesis prefix.

## Upgrade handoff

Storage does not relax version boundaries:

- v1.0.0 through H6,947,499
- v2.0.2 from H6,947,500 through H13,479,999
- v3.0.3 from H13,480,000 onward

Each handoff must reopen the locally derived predecessor state under the exact successor revision and reproduce canonical state. Contradiction fails closed.

## Status

This extension cannot create SOURCE_GATE_PASS by itself. Until contiguous replay and historical coverage qualify, status remains SOURCE_HISTORICAL_REPLAY_BLOCKED.
