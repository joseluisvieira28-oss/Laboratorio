# ARQ-002-CSP-001 — CVD + SWEEP/RECLAIM + POSITIONING — PRE-SOURCE AUTHORITY V0.1

Date: 2026-09-23
Branch: `arq002-cvd-sweep-positioning-v0.1`
State: FROZEN_PRE_SOURCE / RESEARCH_ONLY / OUTCOME_BLIND

## Lineage

Parent archaeology hit:
ARQ-002 — CVD + LIQUIDITY SWEEPS + POSITIONING CONFIRMATION.

This is a NEW prospective child. It does not reopen:
- SCL-AGG-002 generic taker-flow / imbalance family;
- LL-0017 positioning-ratio Discovery;
- LIQUIDATION-PRESSURE-001/002 forced-liquidation line;
- ORDERBOOK-RESILIENCE-001 true L2 refill line;
- L2-RESILIENCY-001 Hyperliquid replenishment mechanism.

## Material distinction

The question is not whether taker imbalance, funding, OI or liquidation pressure predicts price in isolation.

The candidate mechanism is:

1. price crosses a recently established local extreme and reclaims back inside;
2. aggressive flow during the sweep is measured from real Binance USD-M `aggTrades`;
3. OI and funding are used only as contemporaneous crowding confirmation;
4. subsequent reversal is compared between fully confirmed and rejected sweep events.

The historical ARQ-002 idea predates this execution and no exact CVD+sweep+positioning implementation was recovered.

## Terminology boundary

Until true historical order-book depletion is available, this lab must call the event a:

**PRICE SWEEP/RECLAIM PROXY**

It must NOT be represented as:
- true L2 liquidity depletion;
- order-book refill;
- actual stop inventory;
- liquidation event.

## Asset

Exactly one instrument:
- Binance USD-M BTCUSDT perpetual.

No altcoin/cross-asset search under this LAB_ID.

## Candidate official sources

Public Binance Vision only, zero credentials and zero cash cost:

1. USD-M daily `aggTrades` — aggressive trade direction and quantity.
2. USD-M daily 1m `klines` — deterministic recent extreme and reclaim structure.
3. USD-M daily `metrics` — open-interest state.
4. USD-M monthly `fundingRate` — funding state.
5. Published `.CHECKSUM` sidecars for every acquired archive.

No REST fallback may silently replace archive failures.

## Temporal governance

Source probes may inspect only structure/timestamps on fixed dates in:
- 2022
- 2023
- 2024

Scientific windows are NOT released by this pre-source authority.

Protected:
- 2025 LOCKED
- 2026 FORBIDDEN

No live trading, orders, exchange mutation, wallets, alerts, deployment or main merge.

## Source-only probe dates

Exactly:
- 2022-06-15
- 2023-06-15
- 2024-06-15

For each date verify:
- aggTrades daily ZIP + CHECKSUM;
- BTCUSDT 1m kline daily ZIP + CHECKSUM;
- BTCUSDT metrics daily ZIP + CHECKSUM;
- corresponding monthly fundingRate ZIP + CHECKSUM;
- ZIP readability;
- schema family;
- timestamps;
- no timestamp >= 2025-01-01;
- no unresolved conflicting duplicate identities.

## Source gate must remain outcome-blind

Allowed:
- archive filenames;
- SHA256/checksum state;
- row counts;
- headers/schema;
- timestamp first/last;
- timestamp cadence distributions;
- duplicate counts;
- whether aggTrade buyer-maker boolean is parseable;
- whether metrics contain OI fields;
- whether funding exposes timestamp and rate fields.

Forbidden:
- price levels;
- quantities;
- signed CVD values;
- OI values;
- funding values;
- returns;
- event outcomes;
- PnL.

## Source terminal states

- SOURCE_DATA_PASS
- SOURCE_DATA_INSUFFICIENT
- SOURCE_SCHEMA_FAIL
- SOURCE_PROVENANCE_FAIL
- TECHNICAL_FAIL_CLOSED

No source outcome is NO_EDGE.

## Post-source rule

If SOURCE_DATA_PASS:
1. freeze exact event clock, recent-extreme window, reclaim semantics, CVD window, OI/funding alignment, costs, Discovery period, inference and promotion gates;
2. only then open economic values.

If source fails:
- do not change provider under this LAB_ID;
- do not relabel a weaker proxy as the same source;
- no outcome access.
