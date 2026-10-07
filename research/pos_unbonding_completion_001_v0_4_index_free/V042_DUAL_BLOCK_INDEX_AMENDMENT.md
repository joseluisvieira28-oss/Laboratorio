# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.4.2 DUAL BLOCK-INDEX AMENDMENT

Date: 2026-10-07
Parent freeze: 71ac365e709b0e0d7074caed7e842f513207aa85
V0.4.1 subspace route: INVALID / CLOSED
Outcomes opened: NO

## New source capability

Before querying any complete_unbonding event counts, V0.4.2 freezes a dual-independent block-index route.

A Comet/Tendermint block_search index may be used for full completion discovery only if two independently operated historical providers satisfy all requirements below.

## Query protocol

For each selected chain and frozen 2023-2024 height interval:
- use JSON-correct HTTP encoding for the block_search query parameter;
- primary event query: complete_unbonding.amount EXISTS bounded by block.height >= first_height and block.height <= last_height;
- paginate deterministically until total_count is exhausted;
- preserve query string, provider, page, response digest, returned block height/time/hash and total_count.

## Completeness bar

Block-index discovery is accepted as a complete-equivalent source route only if:
1. two independent operators both expose historical block_search across the whole frozen interval;
2. each index is fully paginated with no missing/error pages;
3. both providers return exactly the same ordered set of canonical block heights for the primary query;
4. canonical block hashes/timestamps match on every returned height when checked against raw /block;
5. complete_unbonding events at returned heights are read from canonical /block_results, not inferred from the index payload alone;
6. deterministic raw audits below show no complete_unbonding block omitted by either index.

If the two complete result sets differ, the chain fails this route.

## Raw audit schedule

Before event counts are inspected, raw audit windows are fixed as follows for every selected chain and each calendar month in the frozen interval:
- find the first canonical block at or after 00:00:00 UTC on the 1st day of the month;
- inspect block_results exhaustively for that block and the next 511 canonical heights;
- record every complete_unbonding event seen;
- require every audited event-bearing height to be present in both independent block_search result sets.

The 512-block audit window is a source-integrity diagnostic and cannot change after observed counts.

## Cohort reconstruction

For each discovered actual completion height:
- block_results is the authority for final release event attributes;
- query the historical staking record for the event delegator/validator pair at H-1 where supported, using a versioned exact-key or version-pinned gRPC query;
- recover creation_height/completion_time/balance when possible;
- verify the initiation at creation_height in raw TxRaw;
- resolve cancellation, slash and hold effects fail-closed.

## Gates unchanged

Materiality remains 10 bps of historical bonded stake.
Sample bar remains >=40 MATERIAL chain-days TOTAL across >=5 chains.
No market outcomes may be read in V0.4.2.
