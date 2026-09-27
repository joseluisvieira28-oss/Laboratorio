# POB-HOURLY-STRIKE — KALSHI BOOK SCHEMA TRANSPORT FIX V0.3

Date: 2026-09-27
Status: FROZEN_TRANSPORT_ONLY / OUTCOME_BLIND
Parent: POB_HOURLY_STRIKE_PRE_SOURCE_AUTHORITY_V0.1.md

## Proven schema

Future KXBTCD public order-book diagnostic established:
- top-level key: orderbook_fp
- nested keys: yes_dollars, no_dollars
- each side is a list
- each non-empty level is a two-element array [price, quantity]

No price or quantity values were printed in the diagnostic.

## Authorized normalization

The source probe may normalize:
- Polymarket CLOB: bids / asks
- Kalshi: orderbook_fp.yes_dollars / orderbook_fp.no_dollars

Schema validity and level presence must be recorded separately.
A responsive HTTP endpoint alone is no longer sufficient for source_ready.

No scientific rule, pair selection, time window, strike rule, reference definition, tie boundary, economics or outcome access changes.
