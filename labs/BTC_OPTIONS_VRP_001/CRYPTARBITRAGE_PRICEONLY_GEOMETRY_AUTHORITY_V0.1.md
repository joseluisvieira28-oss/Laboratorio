# BTC-OPTIONS-VRP-001 — CRYPTARBITRAGE PRICE-ONLY COVERAGE DIAGNOSTIC AUTHORITY V0.1

Date: 2026-09-19
Parent source probe: `OVRP-CRYPTARBITRAGE-2024H1-PARQUET-001`
Parent canonical run: `35469141429`
Parent classification: `CRYPTARBITRAGE_2024H1_SOURCE_INSUFFICIENT`

## Why this diagnostic is allowed

The exact free parquet was successfully downloaded and validated as a real parquet with 4,498,832 timestamped rows spanning 2024-01-13 through 2024-07-27. The frozen executable-source gate failed because the file has no bid-size or ask-size columns.

That failure is preserved and cannot be rewritten.

This diagnostic asks a separate source-only question: whether the file contains rich **price-only** historical Deribit BBO geometry in the original 25–35 DTE neighborhood. It does not adjudicate execution feasibility and cannot promote or rescue the old execution MVE.

## Frozen structural checks

Using only the exact public parquet already identified by provenance:

- parse timestamp from `snapshot_time`;
- parse expiry from `expiry_date` and/or `instrument_name`;
- parse strike and call/put right from `instrument_name`;
- require positive bid and ask with ask >= bid;
- count rows with 25 <= DTE <= 35;
- count distinct UTC dates and distinct UTC hours in that band;
- count same-snapshot same-expiry same-strike call+put pairs with positive bid/ask;
- report availability of open interest and volume fields without applying any outcome-dependent threshold.

No bid/ask-size substitute is permitted.
No price values are emitted.
No returns, future realized variance, VRP, PnL, PF or strategy outcome is computed.

## Interpretation classes

- `PRICE_ONLY_GEOMETRY_RICH_EXECUTION_SIZE_BLOCKED`: at least 120 distinct UTC hours and at least 90 distinct UTC dates with positive bid/ask rows in 25–35 DTE, plus at least 120 paired call+put snapshot keys.
- `PRICE_ONLY_GEOMETRY_SPARSE_EXECUTION_SIZE_BLOCKED`: some valid price-only coverage exists but the rich-geometry rule is not met.
- `PRICE_ONLY_GEOMETRY_UNUSABLE`: no valid 25–35 DTE positive bid/ask coverage.

Regardless of class, absence of BBO sizes remains an execution blocker for the old MVE.
