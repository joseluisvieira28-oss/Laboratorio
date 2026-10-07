# V0.7 INDEPENDENT REPLAY FREEZE

POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001
Date: 2026-10-07. Parent: d80bac3e5ef55384a9d5e73541ab650d424d4f5f.
This is a separately frozen genesis replay path. Existing V0.7 source-B/IBC branches are preserved; their proofs do not substitute for execution replay.

## Scope and firewall
Coreum coreum-mainnet-1 only. Completion interval 2023-01-01 through 2024-12-31 UTC. Materiality >=10 bps historical bonded native stake; >=40 MATERIAL chain-days TOTAL across >=5 chains. Actual complete_unbonding is T_completion. Full cancellation/slash/hold reconciliation required. No prices/returns/PnL/market outcomes, trading/orders/wallet/account/private endpoints/spending or main changes. No census, completion counts or outcome analysis until replay validity passes; a Coreum replay pass alone does not satisfy the five-chain global gate. CRO requires a separately committed extension after an exact Coreum blocker.

## Prospective protocol
1. Download official CoreumFoundation genesis for coreum-mainnet-1; pin immutable repository revision, exact bytes SHA256, chain_id, initial_height, initial validators and genesis time before replay.
2. Inventory official historical tags/releases, dependencies, build toolchains and binaries from genesis through H=15,000,000. Pin source commits, downloaded bytes/build receipts and binary SHA256. Derive upgrade names/heights from canonical on-chain upgrade plans and independently executed governance/state; release dates alone are insufficient. Missing or unverified intervals block replay.
3. Source A is the already qualified official historical archive from V0.5. Raw blocks, commits and validator sets may be fetched only as public transport. Its block_results must not supply local ABCI results. Save exact bytes, URL, UTC, status, hash and failures. No random endpoint substitution.
4. Validate every sequential height from genesis; chain ID, parent linkage, locally recomputed consensus header/block hash, DataHash and transaction inclusion, commits and >2/3 validator voting power signatures against evolving validator sets. Unsupported historical signature/hash verification is an explicit unsatisfied gate, never a warning-only pass.
5. Execute InitChain and every historical block using exact versioned application/consensus semantics, including upgrades, BeginBlock/DeliverTx/EndBlock or FinalizeBlock as applicable. Persist local state and local ABCI execution results. Disable validator signing and transaction broadcast; no wallet or private RPC. Never interpret generic RPC block JSON as sufficient executable CometBFT blockstore without an audited importer.
6. Require H=5,000,000 / 10,000,000 / 15,000,000 canonical height/hash/time/AppHash anchors and continuous validation. Account for consensus AppHash offset: header H normally commits state after H-1; compare local post-H Commit to header H+1, with version-specific semantics proved. Fetch H+1 at each anchor. Any mismatch fails closed.
7. Only after full replay validity derive actual complete_unbonding from local execution/state transitions; reconcile cancellations, slash, holds and balances, then compare Source A results. Never infer completion from scheduled queue timestamps.
8. G2 adjudication explicitly separates independent computation from transport. Same-source blocks are not independent transport. Replay plus verified consensus/genesis commitment may support independently computed application evidence, but must demonstrate authenticity, contiguous coverage and reproducibility. No blanket two-provider claim.

## Resource and checkpoint policy
Public/free retrieval only. Do not dispatch paid Actions, buy infrastructure or run a 15M-block job without measured resource feasibility. An operationally unavailable environment is not proof that chain history cannot be replayed. Provide reproducible local Linux/Work build, transport, importer and chunked runner requirements if Actions infeasible. Chunks start only from locally derived verified state, preserving full prefix, version/binary hashes, state/blockstore/results hashes, height, AppHash and predecessor receipt; external pruned snapshots/state-sync are inadmissible substitutes for the genesis prefix.

## Terminal rule
SOURCE_GATE_PASS requires all replay/identity/coverage/cryptographic/application/lifecycle prerequisites relevant to source qualification. Otherwise SOURCE_HISTORICAL_REPLAY_BLOCKED with exact missing artifact or failed operation, commands/receipts, and distinction between transport, build, resource and scientific status. No NO_EDGE or weakened gates. Planning/synthetic checks are not replay success.

