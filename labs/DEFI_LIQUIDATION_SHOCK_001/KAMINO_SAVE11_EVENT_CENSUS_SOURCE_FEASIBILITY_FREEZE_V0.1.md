# DEFI-LIQUIDATION-SHOCK-001 — KAMINO + SAVE11 EVENT CENSUS SOURCE FEASIBILITY FREEZE V0.1

Date: 2026-09-23
Status: FROZEN PRE-EXECUTION / SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED

## Scope

This sub-gate advances only the two liquidation classes whose historical decoder authority and exact RAW-verified first-success boundaries are already closed:

### Kamino Lend
- program: `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`
- instruction: `liquidate_obligation_and_redeem_reserve_collateral`
- discriminator: `b1479abce2854a37`
- authoritative realized-event interval starts: `2023-11-17T14:48:24Z`
- frozen interval ends: `2025-01-01T00:00:00Z` exclusive

### Save / Solend 0x11
- program: `So1endDq2YkqhipRh3WViPa8hdiSpxWy6z3Z6tMCpAo`
- instruction: `LiquidateObligationAndRedeemReserveCollateral`
- native tag: `0x11`
- authoritative realized-event interval starts: `2024-07-19T19:30:52Z`
- frozen interval ends: `2025-01-01T00:00:00Z` exclusive

The first-success transaction itself is included in the eventual authoritative population.

## Existing authority retained

This gate does not alter:
- historical source boundaries;
- program IDs;
- instruction identities;
- transaction success semantics;
- first-success receipts;
- frozen scientific window;
- the existing `BOUNDED_CENSUS_PLAN_V0.1`.

Canonical realized transaction rule remains:
- transaction execution success required;
- failed matching transactions remain `LIQUIDATION_ATTEMPT_FAILED_NOT_REALIZED`;
- metadata inconsistency => `SOURCE_ANOMALY_FAIL_CLOSED`.

## New source-route probe

Candidate free route: `solarchive.org`.

Public documentation states:
- direct historical Solana transaction Parquet;
- no API key / registration / rate limit;
- daily transaction partitions;
- data currently sourced from Solana Foundation BigQuery exports;
- partition `index.json` metadata and HTTP-accessible Parquet files;
- critical transactions may be cross-checked against Solana RPC.

The route is NOT authoritative merely because it exists. It must first pass this source-feasibility gate.

## V0.1 probe allowed actions

1. Fetch only daily `index.json` metadata for every UTC date intersecting the two authoritative intervals.
2. Record:
   - HTTP status;
   - published file count;
   - declared partition bytes when discoverable;
   - file URL metadata.
3. Require complete date-partition availability for the respective interval before claiming route coverage.
4. Open only Parquet metadata/footer for one published file from a Kamino-start date and one from a Save11-start date.
5. Persist the Parquet column schema only.
6. Do NOT read transaction rows in V0.1.
7. Do NOT inspect prices, returns, token prices, market direction, PnL or future outcomes.

## Required schema for promotion to census execution

A viable transaction archive must expose enough raw transaction structure to deterministically recover BOTH:
- outer instructions;
- inner/CPI instructions;

including sufficient information to resolve:
- invoked program ID;
- raw instruction data bytes or an equivalent lossless serialized representation;
- signature;
- slot/block time;
- transaction execution status.

If the archive cannot establish inner/CPI instruction identity, it cannot be the sole source for the authoritative census.

## Classifications

- `SOLARCHIVE_EVENT_CENSUS_ROUTE_PASS`
  - every required date partition exists;
  - schema is sufficient for outer + inner/CPI deterministic decoding.

- `SOLARCHIVE_EVENT_CENSUS_ROUTE_PARTIAL`
  - route exists but date coverage is incomplete OR schema does not expose sufficient inner/CPI instruction data.

- `SOLARCHIVE_EVENT_CENSUS_ROUTE_BLOCKED`
  - metadata/Parquet access technically fails.

- `SOURCE_ANOMALY_FAIL_CLOSED`
  - contradictory dates/schema/metadata.

No `NO_EDGE` classification is possible in this gate.

## Next transition if PASS

Freeze a deterministic DuckDB/Parquet census implementation that:
1. filters only the frozen programs and exact instruction identities;
2. decodes outer + inner/CPI instructions;
3. applies exact transaction-success semantics;
4. deduplicates realized events by transaction signature + instruction location/index;
5. retains failed attempts separately;
6. emits chunk/date completeness receipts;
7. RAW-verifies a prospectively frozen validation sample against official Solana RPC;
8. never opens market outcomes.

## Firewall

prices=false; returns=false; pnl=false; direction=false; economic_outcomes=false; protected_2025_2026_market_outcomes=false; trading=false; orders=false; wallets=false; exchange_mutation=false; paid_source=false; account_creation=false; merge_main=false.
