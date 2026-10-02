# DLS ROUTE A3C — KAMINO MAY 2025 SHARDED TRANSPORT V0.1

Date: 2026-10-02
Status: FROZEN TECHNICAL TRANSPORT / SOURCE ONLY / SCIENCE UNCHANGED

## Reason
The canonical A3B Kamino May-2025 full-program traversal is transport-heavy and has remained in progress for an extended period. This addendum changes only transport parallelization.

## Parent authority
Inherit exactly:
- DLS_ROUTE_A3B_STREAMING_PROGRAM_TRANSPORT_ADDENDUM_V0.1.md
- Route A3 gTFA equivalence PASS run 36969189081
- A2 four-class equivalence PASS run 36900517788
- Kamino shape conformance correction commit 8d9eb09b0f5319f155d38caae6d2c3079ed13b5c

## Exact month
Canonical scientific partition:
[2025-05-01T00:00:00Z, 2025-06-01T00:00:00Z)

Transport-only fixed shards:
0. [2025-05-01T00:00:00Z, 2025-05-09T00:00:00Z)
1. [2025-05-09T00:00:00Z, 2025-05-17T00:00:00Z)
2. [2025-05-17T00:00:00Z, 2025-05-25T00:00:00Z)
3. [2025-05-25T00:00:00Z, 2025-06-01T00:00:00Z)

They are contiguous, non-overlapping and exactly cover the frozen month.

## Per-shard source semantics
Identical A3B:
- exact frozen Kamino program ID
- getTransactionsForAddress
- transactionDetails=full
- sortOrder=asc
- limit=1000
- exact shard blockTime filter
- status=succeeded
- paginationToken to terminal absence
- A2 canonical RAW normalizer
- frozen Kamino discriminator
- corrected canonical 2025 shape only
- exact instruction path required
- direct frozen collateral mint role account[8]
- no event sampling or truncation.

## Merge gate
Canonical May receipt may be emitted only if:
- 4/4 exact shard identities are present;
- all 4 classify SHARD_SOURCE_PASS;
- boundaries are exactly contiguous and exhaustive;
- every row timestamp lies inside its shard;
- zero canonical instruction duplicates across shards;
- zero errors;
- deterministic merged sorting by timestamp/signature/instructionAddress.

The merged scientific receipt uses the same V0.2 protocol-source schema and canonical May window as A3B.

## Firewall
market_data_read=false
prices_2025_opened=false
returns_2025_opened=false
pnl_2025_opened=false
prices_2026_opened=false
post_outcome_tuning=false
purchases=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
merge_main=false
trading_authority=NONE
