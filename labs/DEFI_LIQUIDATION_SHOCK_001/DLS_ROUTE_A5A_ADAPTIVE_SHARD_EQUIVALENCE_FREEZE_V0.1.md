# DLS ROUTE A5A — ADAPTIVE-SHARDED SOL ACCOUNT EQUIVALENCE FREEZE V0.1

Date: 2026-10-02
Status: FROZEN SOURCE/TRANSPORT ONLY — PROTECTED 2025 OUTCOMES CLOSED
Branch: dls-field-enrichment-v01

## Parent evidence

Route A5 annual capacity run 36970950821 proved that five source-authoritative SOL accounts exceed
25,000 successful transactions in the 2024 annual window.

Route A5M run 36971541130 then failed only because the frozen monthly shard for:
- marginfi / CCKtUs6Cgwo4aaQUmBPmyoApH2gUDErxNZCAntD6LYGh / 2024-01
exceeded the 25-page transport ceiling.

A5M stopped before scientific equivalence adjudication:
- canonical clusters: 9,931
- reconstructed clusters: 0
- error: account_shard_page_ceiling
- protected 2025 acquisition: false
- prices/returns/PnL: false

This is a transport-density blocker, not scientific divergence.

## Scientific identity — unchanged

Inherit exactly DLS_ROUTE_A5_SOL_ACCOUNT_FILTER_EQUIVALENCE_FREEZE_V0.1:
- the same 13 source-authoritative SOL role accounts;
- the same four frozen classes: marginfi, save0c, kamino, save11;
- the same A2-validated RAW normalizer;
- the same program IDs/discriminators;
- the same canonical shape rules;
- the same exact role-account conditions;
- the same SOL market identity;
- the same 60-second clustering;
- the same canonical 2024 OOS truth: 9,931 clusters;
- the same cluster-id construction.

No new account, protocol, decoder, event or role is selected.

## Adaptive transport rule

Initial intervals:
- boundary shard: [2023-12-31T00:00:00Z, 2024-01-01T00:00:00Z)
- the 12 exact UTC calendar months of 2024.

For each (role-account, interval):

1. Probe Helius getTransactionsForAddress with:
   - transactionDetails=signatures
   - sortOrder=asc
   - limit=1000
   - status=succeeded
   - exact blockTime [start,end)
   - at most 8 non-empty pages.

2. If pagination terminates within 8 pages:
   the interval is a LEAF.

3. If pagination does not terminate within 8 pages:
   split the exact interval at integer Unix-second midpoint:
   left=[start,mid), right=[mid,end)
   and recurse deterministically.

4. Minimum leaf duration = 900 seconds.
   If an interval <=900 seconds still exceeds 8 pages:
   ROUTE_A5A_TRANSPORT_BLOCKED.

5. Maximum recursion depth = 16.
   Exhaustion => BLOCKED.

No interval is dropped. The recursive leaves must form a complete, non-overlapping exact partition
of every initial interval.

## Full payload acquisition

Only for a completed LEAF:
- repeat the identical gTFA filter with transactionDetails=full;
- page to terminal pagination;
- full transaction count must equal signatures-probe count;
- no page may escape the frozen interval;
- duplicate signature copies from multiple role-account queries must normalize byte/JSON-stably;
- capability/transport exhaustion => BLOCKED.

This signatures-first split is a transport optimization only.

## Ordering

Relevant source-event order:
1. blockTime
2. slot
3. transaction index
4. instructionAddress lexicographic

If transaction index is absent and multiple relevant signatures share one protocol+slot,
read-only getBlock(transactionDetails=signatures) may be used solely to recover blockchain order.

## Exact 2024 equivalence gate

ROUTE_A5A_SOL_ACCOUNT_EQUIVALENCE_PASS requires ALL:
- canonical OOS SOL cluster count = 9,931;
- reconstructed OOS SOL cluster count = 9,931;
- exact cluster_id set equality;
- missing cluster IDs = 0;
- extra cluster IDs = 0;
- every common cluster exactly matches:
  protocol, instruction_class, market, first/last timestamps, T0,
  event_count, distinct signature count, first/last signature;
- relevant decoder/shape/role/order conflicts = 0;
- duplicate canonical instruction conflicts = 0;
- adaptive interval coverage gaps/overlaps = 0.

Anything else:
ROUTE_A5A_SOL_ACCOUNT_EQUIVALENCE_BLOCKED.

## 2025 firewall

This run is 2024 source equivalence only.

Even PASS does NOT authorize protected 2025 acquisition until a separate source-only
2025 SOL-account registry extension gate proves the complete 2025 account set.

No 2025/2026 prices, returns, PnL or economic outcomes.
No purchase or provider upgrade.
No main merge.
No live trading/orders/wallet/exchange mutation.
Trading authority: NONE.
