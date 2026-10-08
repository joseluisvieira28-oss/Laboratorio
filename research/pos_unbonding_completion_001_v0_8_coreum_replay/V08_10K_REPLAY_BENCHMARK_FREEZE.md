# V0.8 10K REPLAY BENCHMARK FREEZE

Candidate: POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001  
Date: 2026-10-08  
Scope: Coreum source/replay tooling only.

## Frozen benchmark

Replay Coreum mainnet H1 through H10,000 from the frozen genesis using pinned v1.0.0 source.

Execution is split prospectively:

- chunk A: H1-H5,000
- close/reopen application + consensus databases
- chunk B: H5,001-H10,000
- retain H10,001 header for final AppHash offset

Raw block acquisition uses only the frozen archive transport and the receipt-complete range fetcher. No remote block_results.

## Required checks

PASS requires all of the following:

1. exact chain-id at every height;
2. no predecessor gap;
3. locally decoded block hash equals transported BlockID hash;
4. native BlockExecutor validation succeeds sequentially;
5. every local post-H AppHash equals header H+1 AppHash;
6. local ABCI response exists for every applied height;
7. DeliverTx response count equals raw block tx count;
8. resume at H5,001 reopens exact persisted state without InitChain;
9. raw bytes are losslessly packaged with per-file SHA256;
10. local ABCI database values are exported with per-height SHA256 before pruning;
11. historical per-height ABCI keys are pruned only after export verification;
12. lastABCIResponseKey remains at H10,000;
13. final local state/home checkpoint manifest is produced with aggregate hashes.

## Metrics frozen before run

Record separately:

- raw acquisition elapsed seconds / blocks per second / bytes;
- replay elapsed seconds / blocks per second;
- raw package bytes;
- local ABCI archive bytes;
- application DB bytes;
- consensus state DB bytes before and after ABCI pruning;
- home bytes;
- transaction-bearing block count and total transactions;
- evidence-bearing block count.

## Fail closed

Any missing height, terminal transport failure, decode/hash mismatch, commit/state validation failure, AppHash mismatch, missing ABCI response, resume failure or archive/checkpoint hash mismatch fails the benchmark.

A 10K PASS is an operational scaling milestone only. It is not SOURCE_GATE_PASS and authorizes no census or outcomes.
