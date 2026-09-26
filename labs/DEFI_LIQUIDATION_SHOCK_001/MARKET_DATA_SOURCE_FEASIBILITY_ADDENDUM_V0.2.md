# DEFI-LIQUIDATION-SHOCK-001 — MARKET DATA SOURCE FEASIBILITY ADDENDUM V0.2

Date: 2026-09-27
Status: FROZEN / OUTCOME-BLIND / PRE-DISCOVERY

## Purpose

Clarify what MARKET_DATA_SOURCE_PASS means before FINAL_PRE_DISCOVERY_AUTHORITY_PASS.

Pre-authority source feasibility MUST NOT open candle price values.

## Pre-authority permitted evidence

For a prospectively mapped direct market, the feasibility gate may inspect only:

- exchange/public-source product metadata;
- source documentation;
- instrument identity and quote asset;
- listing/delisting metadata when available;
- archive object existence through metadata/HEAD requests;
- archive object size;
- companion checksum object existence;
- HTTP status / pagination availability;
- filenames/date keys;
- source route reproducibility.

It MUST NOT:
- download or decompress kline/candle payloads;
- read OHLC values;
- compute returns/volatility;
- rank sources by later response.

## MARKET_DATA_SOURCE_PASS semantics

Before outcomes, PASS means:

1. every market selected for inferential eligibility has a direct source mapping fixed prospectively;
2. source precedence follows MARKET_DATA_SOURCE_GATE_FREEZE_V0.1;
3. product/listing boundary is source-supported;
4. required historical route/archive availability is proven at metadata level for the intended experiment interval;
5. source identifiers and date boundaries are frozen;
6. no price payload has been opened.

This is a route/availability authority, not a statement that every candle payload has already passed content QA.

## Post-authority acquisition gate

Only after FINAL_PRE_DISCOVERY_AUTHORITY_PASS may the lab download/decompress 2021-2024 market bars.

Before computing any event return, the acquisition layer must then enforce:

- checksum verification;
- exact UTC minute keys;
- duplicate count;
- non-monotonic count;
- missing required bars;
- deterministic archive/API reconciliation;
- coverage thresholds from OUTCOME_STATISTICAL_AUTHORITY_FREEZE_V0.1.

If these fail:
`MARKET_DATA_SOURCE_BLOCKED`

No event-return hypothesis is considered tested.

## Protected period

Metadata queries must not be used to fetch 2025/2026 price payloads.

2025/2026 market outcomes remain CLOSED.

## Firewall

archive_payload_downloaded=false
candles_opened=false
prices_opened=false
returns_computed=false
pnl_computed=false
economic_outcomes_opened=false
protected_2025_2026_opened=false
post_outcome_tuning=false
live_trading=false
merge_main=false
