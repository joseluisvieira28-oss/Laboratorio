# Crypto Lab — Next Mine Data Feasibility Scan

Audit date: 2026-09-21  
Repository: `joseluisvieira28-oss/Laboratorio`  
Decision basis: data quality, source quality, auditability and non-duplication only

## Decision

The repository contains many branches but few independent, unresolved mechanisms with a
complete public source path. The scan inspected 249 remote branches, the current local tree,
the branch census, active deployment registry, protected-research registry, archive registry,
status markers and candidate closeouts. Branches were collapsed into economic/informational
families before classification.

**One clean new attack is identified:** `STETH-REDEMPTION-BASIS-002`, classified
`DATA_READY_WITH_CONTROLS`.

Its predecessor, `STETH-REDEMPTION-BASIS-001`, remains closed for its exact pre-activation
source boundary. V0.2 is a separately identified successor with a new prospective source
clock. Its source gate passed before outcomes, and its exact pre-Discovery protocol is frozen.

No performance, PnL, return, win-rate, Sharpe or apparent attractiveness was used to select
it. Existing forward/shadow candidates with defensible data remain active under their own
authorities and are not presented as new mines.

## Scope and method

The inventory covered:

- 249 remote branches present on 2026-09-21;
- 407 non-cache files in the local closeout lineage;
- active deployment, nonterminal, protected-research and archive registries;
- source contracts, source closeouts, manifests, freezes, receipts and terminal markers;
- repository families under `research/`, `labs/`, `governance/`, workflows and registries.

Protected datasets were not opened. Where a status document contained prior outcome fields,
only the state label, source lineage and governance boundary were used. No outcome value
entered ranking or readiness classification.

## Classification summary

The authoritative matrix contains 60 unique candidates. The consistency test produces:

| Classification | Count |
| --- | ---: |
| `SCIENTIFICALLY_CLOSED` | 22 |
| `SOURCE_BLOCKED` | 14 |
| `DUPLICATE` | 5 |
| `DATA_FRAGILE` | 4 |
| `SOURCE_PROBE_REQUIRED` | 7 |
| `DATA_READY` | 0 |
| `DATA_READY_WITH_CONTROLS` | 8 |

Seven of the eight `DATA_READY_WITH_CONTROLS` candidates are already in an authorized
forward, shadow or validation workflow. They remain ready in source terms, but are not new
mines. `STETH-REDEMPTION-BASIS-002` is the sole unresolved, distinct candidate selected for
a new attack.

Important findings:

- Trend, classic-indicator, generic lead-lag and generic carry variants are saturated or
  economically equivalent to existing work.
- Event families often fail on immutable event identity rather than market-data availability.
- On-chain state/log sources can be point-in-time correct, but historical state calls require
  archive capability, exact block mapping and provider quorum.
- Binance Data Vision is the strongest exchange archive in the repository because raw ZIPs,
  timestamps and companion SHA-256 checksum files can be preserved. Its own documentation
  warns that archived files may later be replaced, so original ZIP plus contemporaneous
  checksum and retrieval receipt are mandatory.
- SQD provides bounded Ethereum streams with explicit `fromBlock`/`toBlock` pagination and
  finalized-chain handling. It is strong for logs, but it does not replace historical
  contract-state calls.
- Xatu is a credible open Ethereum consensus-data route, but the exact validator table,
  temporal alignment and protected-safe partitions still require the frozen four-date probe.

## Top candidate

### Candidate A

Candidate ID: `STETH-REDEMPTION-BASIS-002`  
Family: MR / RV  
Status: `DATA_READY_WITH_CONTROLS`  
Data source: Ethereum mainnet historical state/logs through three public archive-capable RPC
routes plus SQD Ethereum-mainnet bounded log streams  
Coverage: 2023-05-16 through 2024-12-31  
Resolution: one deterministic 12:00 UTC snapshot per day; block/event resolution beneath it

Why data is defensible:

- the source boundary was frozen from the independently proven Lido V2 activation block,
  before economic outcomes;
- chain ID, activation receipt, edge block mapping, bytecode and historical calls require a
  two-of-three provider quorum;
- contract identities, event signatures and the first/last snapshot are fixed;
- SQD requests are bounded by block range and the source code rejects timestamps beyond the
  protected ceiling;
- source artifacts and canonical identities are hashable;
- Ethereum history is append-only after finality, allowing byte-preserving evidence receipts.

Required controls:

- retain raw JSON/JSONL response bytes before normalization and SHA-256 every object;
- record provider, request body, response status, retrieval time and block hash;
- require two-of-three agreement for historical state and timestamp-to-block mapping;
- preserve SQD pagination boundaries and reject gaps, reversals or rows outside the request;
- enforce the 2024-12-31 ceiling before every network request;
- bind the exact source receipt, implementation freeze and pre-Discovery protocol;
- treat HTTP 429/5xx only as transport failures; never change the source clock or rules;
- verify that no admissible canonical closeout already exists before consuming the one-shot.

Duplication check: `DISTINCT`. It uses an explicit Lido redemption/queue cash-flow anchor.
It is not ETH validator-flow pressure, stablecoin peg reversion, generic staking yield or the
closed pre-activation `STETH-REDEMPTION-BASIS-001` boundary.

Known source risks: free RPC rate limits, provider pruning/inconsistent historical-call
support, timestamp-to-block disagreement, SQD pagination truncation and accidental use of a
noncanonical retry.

Required freeze before outcomes: already present in
`STETH_REDEMPTION_BASIS_002_FINAL_PRE_DISCOVERY_PROTOCOL_V0_1.md`; the run must verify exact
hash binding and canonical precedence before it can read economic results.

Smallest next scientific experiment: run one canonical transport-remediated Discovery using
the frozen 596-snapshot population and unchanged implementation. If transport or provenance
fails, close as technical/provenance failure. Do not inspect or substitute noncanonical runs.

### Candidate B

Not selected. Other `DATA_READY_WITH_CONTROLS` rows are already in prospective forward/shadow
or validation workflows. Starting a second historical mine would duplicate active work.

### Candidate C

Not selected. Remaining distinct mechanisms require a source probe or are source-fragile,
blocked or scientifically closed.

## Strongest source-probe queue, not ready candidates

1. `ETH-STAKING-FLOW-001-XATU`: public Xatu canonical validator snapshots; execute only the
   frozen four-date temporal/schema probe.
2. `EXCHANGE-DELISTING-SHOCK-001-V04`: official Binance announcement identity plus Data
   Vision market archive; complete the outcome-blind event/source census.
3. `DEFI-LIQUIDATION-SHOCK-001`: BigQuery candidate census plus raw archival RPC
   reconciliation; remains closed to Discovery until protocol coverage passes.

These are not promoted to `DATA_READY` by documentation alone.

## Primary-source observations

- [Ethereum JSON-RPC](https://ethereum.org/developers/docs/apis/json-rpc/) documents explicit
  historical block parameters and the distinction between state and historical methods.
- [SQD EVM API](https://docs.sqd.dev/en/api/evm/introduction) exposes bounded block streams,
  pagination rules and finalized/reorg handling.
- [Xatu Data](https://ethpandaops.io/data/xatu/) describes open Ethereum beacon, canonical
  chain, mempool and related datasets.
- [Binance Public Data](https://github.com/binance/binance-public-data) documents daily/monthly
  archives, schemas, companion checksums and the fact that archives can later be updated.

Documentation supports capability only. Repository receipts and exact-event/source probes
remain the acceptance authority.

## Governance outcome

- News Shock V0.3 remains `SOURCE_BLOCKED`; no consensus research was repeated.
- No closeout, threshold, hierarchy or scientific decision was altered.
- No Drive access occurred.
- No protected dataset, 2026 holdout, wallet, order or exchange mutation was accessed.
- No merge to `main` is authorized or performed.

## Final result

`CLEAN NEXT MINE IDENTIFIED — ONE CANDIDATE ONLY`

Recommended next attack: `STETH-REDEMPTION-BASIS-002`, on data/source basis only.
