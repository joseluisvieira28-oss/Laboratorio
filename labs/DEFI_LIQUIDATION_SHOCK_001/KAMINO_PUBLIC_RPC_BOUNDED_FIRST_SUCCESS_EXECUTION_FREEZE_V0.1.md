# DEFI-LIQUIDATION-SHOCK-001 — KAMINO PUBLIC RPC BOUNDED FIRST-SUCCESS EXECUTION FREEZE V0.1

Date: 2026-09-22  
Branch: `defi-liquidation-kamino-boundary-execution-v0.1`  
Status: **FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED**  
Change class: **PRE-OUTCOME TECHNICAL SOURCE-TRANSPORT SUPERSESSION**

## Authority preserved

This freeze does not alter the scientific contract in:
- `ONCHAIN_FIRST_SUCCESS_BOUNDARY_PLAN_V0.1.md`
- `FIRST_SUCCESS_BOUNDARY_IMPLEMENTATION_FREEZE_V0.1.md`
- `HISTORICAL_DECODER_AUTHORITY_MATRIX_V0.2.md`

The following remain unchanged:
- protocol: Kamino Lend;
- program ID: `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`;
- class: `liquidate_obligation_and_redeem_reserve_collateral`;
- discriminator: `b1479abce2854a37`;
- source-supported boundary: `2023-11-17T13:25:35Z`;
- frozen end: `2025-01-01T00:00:00Z`;
- maximum chunk width: 7 days;
- chunk order: strictly ascending;
- success semantics: realized only when transaction `meta.err == null`;
- first-success rule: earliest successful matching transaction in the earliest chronological chunk containing a successful match;
- RAW verification: mandatory before accepting the boundary.

The retired typo `b1479acce2854a37` remains forbidden.

## Why transport supersession is justified

The canonical BigQuery route is operationally unavailable in the current GitHub runtime:
- zero-cost credential presence preflight run `35687938370`;
- result: `BIGQUERY_CREDENTIAL_ABSENT`;
- result: `BIGQUERY_PROJECT_HINT_ABSENT`;
- no BigQuery query or dry-run was executed;
- no billing mutation occurred.

The official public Solana mainnet RPC was then tested source-only.

History-depth probe run `35688049142` showed ordinary reverse pagination is too dense:
- 100 pages;
- 100,000 Kamino-address signatures;
- moved only from 2024-12-15T07:32:56Z to 2024-12-12T13:17:00Z;
- classification: `KAMINO_PUBLIC_RPC_HISTORY_PAGE_LIMIT_BEFORE_BOUNDARY`.

Arbitrary-cursor semantics probe run `35688355138` established a bounded alternative:
- exact chunk #1 start blockTime located at `2023-11-17T13:25:35Z`, slot `230561475`;
- exact chunk #1 end blockTime located at `2023-11-24T13:25:35Z`, slot `231964523`;
- ordinary finalized transaction signatures from those blocks were accepted as `until` / `before` cursors by `getSignaturesForAddress`;
- returned Kamino-address signatures remained inside the exact frozen interval;
- classification: `KAMINO_PUBLIC_RPC_ARBITRARY_CURSOR_BOUNDED_WINDOW_SUPPORTED`.

Therefore only the indexed transport changes. Scientific selection, decoder, chronology and acceptance rules do not.

## Frozen public-RPC execution

Endpoint:
`https://api.mainnet-beta.solana.com`

### Phase A — complete bounded signature enumeration

For each frozen 7-day Kamino chunk, beginning with chunk #1:

1. locate the exact start and end blockTime slots deterministically with `getBlockTime`;
2. obtain one finalized ordinary transaction signature from each exact boundary block using `getBlock(transactionDetails=signatures)`;
3. call `getSignaturesForAddress(KaminoProgram)` with:
   - `before = end-boundary ordinary signature`;
   - `until = start-boundary ordinary signature`;
   - `limit = 1000`;
4. continue pagination using the final returned Kamino signature as the next `before`, preserving the same `until`;
5. stop only when the bounded interval is exhausted;
6. fail closed on repeated cursor, non-monotonic pagination, duplicate signature, transport/RPC failure, missing blockTime, or any row outside the frozen interval;
7. retain every returned signature, slot, blockTime, err and memo metadata unchanged.

Completeness receipt must record:
- pages;
- total rows;
- unique signatures;
- duplicates;
- newest/oldest blockTime;
- exact frozen interval;
- terminal page condition.

### Phase B — exhaustive transaction-body decoding

Only after Phase A completeness passes:

1. fetch every enumerated signature with `getTransaction`, finalized, `jsonParsed`, max supported transaction version 0;
2. preserve each raw RPC response byte-for-byte as JSON evidence;
3. inspect top-level and inner instructions;
4. a Kamino liquidation reference match requires:
   - exact program ID; and
   - base58-decoded instruction data beginning with exact discriminator `b1479abce2854a37`;
5. classify:
   - `meta.err == null` => successful realized reference;
   - `meta.err != null` => failed attempt, not realized;
   - any structural ambiguity => source anomaly fail-closed.

No candidate may be silently skipped because its transaction body is unavailable.

### Phase C — first-success adjudication

If chunk contains one or more successful realized matching references:
- select the earliest UTC successful row only after exhaustive chunk decoding completes;
- RAW-verify that exact earliest transaction independently against the preserved response / fresh exact `getTransaction`;
- if RAW passes, its transaction timestamp becomes Kamino's on-chain first-success boundary;
- stop later Kamino chunks.

If chunk contains zero successful realized matching references:
- record a source-only zero-success chunk receipt;
- proceed to the next frozen Kamino chunk in strict ascending order.

If transport/completeness/structural verification fails:
- remain source-blocked;
- do not skip to a later chunk.

## Chunk #1 frozen execution target

- sequence: 1
- start inclusive: `2023-11-17T13:25:35Z`
- end exclusive: `2023-11-24T13:25:35Z`
- candidate SQL authority remains `BIGQUERY_BOUNDED_CANDIDATE_CENSUS_V0_3.sql` for scientific semantics, even though indexed BigQuery transport is superseded here by exact official-RPC reconstruction.

## Explicit non-changes

- no protocol addition/removal;
- no date/window change;
- no discriminator change;
- no success-definition change;
- no sample threshold;
- no event-size threshold;
- no market-data source;
- no economic labels;
- no price data;
- no future returns;
- no PnL;
- no direction;
- no post-outcome tuning.

## Firewalls

- 2025/2026 market outcomes opened: false
- prices queried: false
- returns computed: false
- PnL computed: false
- direction tested: false
- live trading: false
- orders: false
- wallets: false
- exchange mutation: false
- paid source: false
- merge main: false
