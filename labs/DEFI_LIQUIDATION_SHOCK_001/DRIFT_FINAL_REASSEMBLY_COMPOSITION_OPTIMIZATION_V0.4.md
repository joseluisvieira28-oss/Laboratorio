# DEFI-LIQUIDATION-SHOCK-001 — DRIFT FINAL REASSEMBLY COMPOSITION OPTIMIZATION V0.4

Date: 2026-09-26
Status: FROZEN TECHNICAL OPTIMIZATION / SOURCE-ONLY / OUTCOME-BLIND

## Trigger

Disk-backed V0.3 final aggregation is scientifically safe but performs unnecessary database writes for every
failed liquidation attempt. Accepted source chunks already contain deterministic per-chunk deduplication and
the reconstructed chronology requires non-overlapping exact UTC slices.

## Compositional authority

For an admitted chunk:
- chunk SHA256 is verified;
- classification is SOURCE_CHUNK_PASS;
- stream_complete=true;
- anomaly_count=0;
- the frozen collector already deduplicated canonical instruction keys inside that exact slice.

The final reassembler independently proves admitted slices are:
- exact;
- gap-free;
- overlap-free;
- duplicate-slice-free.

An instruction has one authoritative block timestamp. Therefore the same canonical instruction cannot belong
to two disjoint exact UTC slices.

Consequently global event counts may be composed from accepted chunks without writing every failed row into a
cross-slice dedup database.

## V0.4 aggregation rule

First pass over accepted chunk rows:
- validate every row classification and timestamp window;
- count successful / failed by frozen class;
- retain exact distinct successful signature sets only;
- retain first/last successful rows;
- maintain deterministic SHA256-ranked candidate signatures.

Failed rows are counted but not retained after each chunk.

Second pass:
- read only rows whose signature is selected for deterministic RAW reconciliation;
- collect exact instruction addresses and outer/inner path classes.

## Duplicate rule

- within-slice duplicates remain governed by the frozen collector and its anomaly-free chunk receipt;
- cross-slice duplicates are structurally impossible only after exact no-overlap chronology passes;
- any overlap or duplicate slice blocks V0.4 fail-closed.

No event is removed or selected based on market outcome.

## Scientific invariants unchanged

Unchanged:
- program ID;
- four class discriminators;
- source window;
- exact UTC membership;
- success/failure semantics;
- canonical identity;
- source evidence selection;
- RAW sample algorithm;
- RAW authority;
- final PASS criteria;
- economic firewall.

## Firewall

prices=false
returns=false
pnl=false
direction=false
economic_outcomes=false
balances=false
token_amounts=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
account_creation=false
post_outcome_tuning=false
merge_main=false
