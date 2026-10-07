# V0.8 COREUM REPLAY EXECUTION FREEZE

Candidate: POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001  
Date: 2026-10-07  
Parent published V0.7 state: 3946995cdcabc0a2b2c153715ce8515f4c25f93c  
Inherited V0.7 freeze: 8bc913d321e5063480f33a67b705193269aac603

## Purpose

This is a prospective execution/tooling continuation of V0.7. It does not rewrite V0.6/V0.7 and does not authorize census, completion counts, prices, returns, PnL, market outcomes or any trading/account activity.

The immediate question is whether an independently executed/reconstructed Coreum historical Source B can be made reproducible from public/free inputs.

## Frozen scientific boundary

- Chain: Coreum `coreum-mainnet-1` first.
- Completion interval remains 2023-01-01 through 2024-12-31 UTC.
- `T_completion` remains actual canonical lifecycle completion, not scheduled maturity.
- Materiality remains `M_d = R_d / B_d >= 0.001`.
- Global hard gate remains >=40 MATERIAL chain-days TOTAL across >=5 chains.
- No outcome opening before a later PRE-OUTCOME FREEZE after source qualification.
- No weakening of G2, no endpoint hostname relabelling, no use of `/store/staking/subspace` as historical state.

## Execution architecture frozen before run

1. Use only standard GitHub-hosted Linux runners on this public repository or another demonstrably zero-cost Linux environment. No larger/billable runners, no paid infrastructure, no storage purchases.
2. Preserve V0.7 official genesis pin:
   - revision `47b7632f4236ec86ffacbfe882524f82b19b398f`
   - chain-id `coreum-mainnet-1`
   - SHA256 `5be3b3e0fee69842c4c73eb5f54eb64684420736473f0f5cef0ba6b81d44f253`
3. Preserve V0.7 Source A transport endpoint exactly:
   `https://archive.rpc.mainnet-1.tx.org`
   Raw blocks/commits/validator sets may be used as public transport. No `block_results` may be used to supply local ABCI outcomes.
4. Historical binary/source candidates are version-pinned. Mainnet activation must be proved from canonical chain evidence/local execution, not release date alone.
5. Typed block decoding/hash verification must use the consensus library pinned by the corresponding Coreum source revision:
   - V1/Tendermint 0.34.x semantics
   - V2 pinned replacement semantics from its `go.mod`
   - V3/CometBFT 0.37.x semantics
6. Fixed-height verification targets remain H=5,000,000 / 10,000,000 / 15,000,000 plus H+1 for AppHash offset checks.
7. Before any large replay, perform bounded probes:
   - binary/toolchain execution on clean Linux;
   - typed decode/hash/DataHash checks on frozen sparse blocks;
   - full validator pagination and commit-signature verification at sampled heights;
   - authenticated upgrade-ledger discovery;
   - a small genesis-prefix execution pilot only after the executor is implemented.
8. No snapshot or state-sync injection may replace the genesis prefix. Resume is permitted only from locally produced, hash-verified checkpoints.
9. A replay/checkpoint pass requires at minimum chain-id, height, canonical block/header hash, block time and AppHash with the correct H -> H+1 commit offset, plus continuous predecessor receipts.
10. A Source-B qualification attempt after checkpoint reproduction must additionally establish continuous historical coverage sufficient for census: raw blocks, txs, local ABCI/finalize/end-block equivalent results, staking completion evidence and explicit no-gap verification.

## Mainnet upgrade hypotheses allowed only as discovery hints

Inherited Source-A hints:
- plan `v2`: reported applied height 6,947,500
- plan `v3`: reported applied height 13,480,000
- `v2patch1`, `v3patch1`, `v3patch2`: no applied value at H=15,000,000

These are not accepted as independent proof. Source code comments indicate patch plans were intended for testnet. V0.8 must authenticate the mainnet sequence using canonical governance/upgrade evidence and/or locally executed state.

## Fail-closed verdicts

Allowed next verdicts:
- `SOURCE_GATE_PASS`
- `SOURCE_HISTORICAL_REPLAY_BLOCKED`
- `SOURCE_HISTORICAL_COVERAGE_BLOCKED`
- `OPERATIONAL_BLOCKED`

`NO_EDGE` is forbidden because no market outcome/census is authorized here.

A blocker is only terminal for this run if the exact command/input/version/failure is preserved and reproducible. Missing tooling must first be attacked by building the tooling.
