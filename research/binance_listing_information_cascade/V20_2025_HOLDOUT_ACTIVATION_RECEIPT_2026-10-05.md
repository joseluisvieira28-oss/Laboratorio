# V2.0 2025 HOLDOUT ACTIVATION RECEIPT
Date: 2026-10-05
Status: AUTHORIZED TO OPEN FROZEN 2025 OUTCOMES ONCE

## Parent freeze
V2.0 pre-outcome freeze:
7baa29f41260470ed78fb8d9e92bbcdabc8446b4

## SYRUP / LBank source gate
PASS.
Recorded by:
V20_SYRUP_LBANK_SOURCE_GATE_PASS_RECEIPT_2026-10-05.md

## Final all-binding source-only preflight
GitHub Actions run:
37361521676

Pinned execution SHA:
dd5955746f309c1260b9220b8a1e793494f81ee5

Result:
- n = 12
- all_ok = true
- every binding source_ok = true
- every binding asset_required_bars_present = true
- every binding btc_required_bars_present = true
- every binding hist_gaps = 0
- every binding baseline_median_volume_positive = true
- every binding first5 = 5
- every binding hist_minutes = 1380
- every binding hist_5m_chunks = 276

## Exact bindings now activated
- AIXBT -> KUCOIN spot
- CGPT -> KUCOIN spot
- COOKIE -> KUCOIN spot
- SYRUP -> LBANK spot
- KMNO -> KUCOIN spot
- PUMP -> KUCOIN spot
- AVNT -> KUCOIN spot
- ASTER -> KUCOIN spot
- GIGGLE -> KUCOIN spot
- F -> KUCOIN spot
- BANK -> BITGET spot
- MET -> KUCOIN spot

No 2025 price return, PnL, MFE, MAE, delayed return or cost-adjusted outcome had been inspected before this receipt.

## Authorized next action
Execute the already-frozen V2.0 2025 holdout exactly ONCE.

No event, T0, venue, horizon, direction, threshold, cost, BTC-relative rule or gate may change after outcomes are opened.

Primary verdict remains:
- SOURCE_BLOCKED if the frozen sources fail at execution time before a valid n=12 result can be produced;
- NO_EXECUTABLE_EDGE_HOLDOUT if n=12 but any frozen primary execution gate fails;
- SURVIVES_EXECUTION_HOLDOUT only if ALL frozen primary execution gates pass.

Research-only.
No trading.
No orders.
No private endpoints.
No account reads.
No wallets.
No merge to main.
