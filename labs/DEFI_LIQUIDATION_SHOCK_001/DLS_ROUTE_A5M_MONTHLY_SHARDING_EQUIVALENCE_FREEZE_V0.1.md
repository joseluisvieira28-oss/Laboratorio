# DLS ROUTE A5M — MONTHLY-SHARDED SOL ACCOUNT EQUIVALENCE FREEZE V0.1

Date: 2026-10-02
Status: FROZEN SOURCE/TRANSPORT ONLY — PROTECTED 2025 OUTCOMES CLOSED

Parent Route A5 annual capacity result:
- run 36970950821 / artifact 11211836925
- classification ROUTE_A5_CAPACITY_BLOCKED
- five high-traffic source accounts exceeded 25,000 successful transactions over the full 2024 year.
This is a transport-density blocker only.

## A5M transport decomposition
Keep EXACTLY the same 13 source-authoritative SOL accounts, protocol roles, canonical decoders and
9,931-cluster 2024 equivalence gate from DLS_ROUTE_A5_SOL_ACCOUNT_FILTER_EQUIVALENCE_FREEZE_V0.1.md.

Change ONLY transport partitioning:
- boundary shard: 2023-12-31T00:00:00Z <= blockTime < 2024-01-01T00:00:00Z
- 12 exact UTC calendar-month shards in 2024
- gTFA transactionDetails=full
- sortOrder=asc
- status=succeeded
- requested limit=1000
- hard ceiling 25 non-empty pages per account/shard
- a terminal empty page is accepted as pagination termination even if the preceding response exposed a cursor.

Observed capability receipt:
run 36971175039 / artifact 11211492049 showed a frozen narrow account returned all 194 expected
full transaction payloads in one response to requested limit=1000. This is transport capability only.

## Deduplication and source ordering
- deduplicate identical transaction signatures across account queries and shard overlap;
- duplicate copies must normalize to identical A2 fidelity;
- each relevant liquidation instruction is identified by (protocol, signature, instructionAddress);
- repeated discovery of the same canonical instruction via more than one filter account is query duplication, not a new event.

Canonical event ordering:
1. blockTime ascending;
2. slot ascending;
3. transaction index within slot ascending;
4. instructionAddress lexicographic within one transaction.

If gTFA does not expose a transaction index and more than one relevant signature from the same
protocol/market occurs in the same slot, query read-only getBlock for that exact slot with
transactionDetails=signatures solely to recover blockchain transaction order.
Failure to resolve exact order => BLOCKED.
No price/outcome data is involved.

## Boundary
The canonical 2024 OOS census contains a first OOS cluster whose realized event occurs
2023-12-31T23:59:58Z and whose T0 is 2024-01-01T00:00:58Z.
The frozen one-day boundary shard is therefore source-completeness transport, not outcome tuning.

After event reconstruction, apply the exact parent 60-second quiet clustering and split by T0:
- OOS iff 2024-01-01T00:00:00Z <= T0 < 2025-01-01T00:00:00Z.
Events outside that split are not compared as OOS.

## Exact PASS gate
ROUTE_A5M_SOL_ACCOUNT_EQUIVALENCE_PASS only if:
- reconstructed OOS SOL cluster count = 9,931;
- canonical OOS SOL cluster count = 9,931;
- cluster_id set equality exact;
- zero missing cluster IDs;
- zero extra cluster IDs;
- every common cluster matches protocol, class, market, first/last timestamps,
  event_count, distinct signature count, first/last signature and T0;
- zero relevant decoder/shape/role/order conflicts.

Any mismatch => ROUTE_A5M_SOL_ACCOUNT_EQUIVALENCE_BLOCKED.

## Firewall
This run is 2024 source-equivalence only.
No protected 2025 source acquisition.
No 2025/2026 prices, returns, PnL, economic outcomes.
No paid upgrade/purchase.
No main merge.
No live trading/orders/wallet/exchange mutation.
Trading authority: NONE.
