# TREASURY-AUCTION-DEMAND-001 — PRE-SOURCE AUTHORITY V0.1

Date: 2026-09-16

## Status

`RESEARCH_ONLY / PROSPECTIVE / OUTCOME_BLIND / SOURCE_GATE_AUTHORIZED`

No live trading. No exchange mutation. No orders. No alerts/webhooks. No main merge. No deployment. No post-outcome tuning. No 2025/2026 access.

## Lab / source gate

- Lab ID: `TREASURY-AUCTION-DEMAND-001`
- Source gate ID: `TAD-COUPON-SOURCE-001`
- Branch: `treasury-auction-demand-v0.1`
- Primary official source: U.S. Treasury Fiscal Data, Treasury Securities Auctions Data, endpoint `/v1/accounting/od/auctions_query`.

## Anti-duplication

Drive, GitHub and project-history reconciliation found no prior canonical Crypto Lab for U.S. Treasury auction bid-to-cover, bidder allocation, dealer takedown or auction-demand shock -> BTC. This is distinct from:

- News Shock FOMC/CPI/NFP event studies;
- `MACRO-TRANSMISSION-001` daily U.S. 2Y + Nasdaq sign regime;
- `USD-NET-LIQUIDITY-001` Fed/TGA/RRP liquidity;
- `INSTITUTIONAL-FLOW-001` CFTC BTC positioning;
- cross-asset VIX-settlement work.

## Economic mechanism — fixed before source rows

A Treasury coupon auction reveals realized demand for U.S. duration at a scheduled event. A fall in bid-to-cover versus the previous auction of the same original tenor is interpreted prospectively as weaker duration demand / tighter funding-risk conditions; a rise is interpreted as stronger demand. The later economic question, if a separate Discovery authority is ever granted, is whether this auction-demand change transmits to subsequent BTC returns.

No auction outcome is selected because of BTC behavior. No yield-tail or threshold optimization is part of this source gate.

## Frozen source population

Auction date interval:

`2021-01-01 <= auction_date <= 2024-12-31`

Include only nominal fixed-rate coupon Treasury securities with:

- `original_security_term` exactly one of: `2-Year`, `3-Year`, `5-Year`, `7-Year`, `10-Year`, `20-Year`, `30-Year`;
- `inflation_index_security == No`;
- `floating_rate == No`.

Bills, TIPS, FRNs, CMBs and any other term are excluded.

Reopenings remain eligible when they retain one of the frozen original terms. The source identity is `(auction_date, cusip)`.

## Required provider fields

Every retained row must contain valid values for:

- `auction_date`
- `cusip`
- `security_type`
- `original_security_term`
- `inflation_index_security`
- `floating_rate`
- `bid_to_cover_ratio`
- `comp_accepted`
- `primary_dealer_accepted`
- `direct_bidder_accepted`
- `indirect_bidder_accepted`
- `total_accepted`
- `total_tendered`

Amounts must be finite and non-negative. `bid_to_cover_ratio` must be finite and strictly positive.

For every retained row, the exact competitive bidder allocation must reconcile:

`primary_dealer_accepted + direct_bidder_accepted + indirect_bidder_accepted == comp_accepted`

A tolerance of at most 1 unit of the provider's raw amount denomination is allowed solely for numeric serialization.

## Source-only derived series

After sorting by `(original_security_term, auction_date, cusip)`, the source gate may compute only:

`delta_bid_to_cover = current bid_to_cover_ratio - previous bid_to_cover_ratio for the same original_security_term`

The first auction for each tenor has no delta. This is source construction, not an economic outcome.

Primary future direction, if separately authorized later:

- `delta_bid_to_cover > 0` -> stronger auction demand / prospective LONG-BTC direction;
- `delta_bid_to_cover < 0` -> weaker auction demand / prospective SHORT-BTC direction;
- `delta_bid_to_cover == 0` -> NO TRADE.

No magnitude threshold, z-score, percentile, auction-tail filter, tenor selection, bidder-share filter or regime filter may be invented after BTC outcomes are opened.

## Frozen Source/Data Gate — all required

1. retained coupon-auction rows `>= 300`;
2. each of the seven frozen original tenors has `>= 40` retained auctions;
3. comparable same-tenor delta rows `>= 280`;
4. zero duplicate `(auction_date, cusip)` identities;
5. zero invalid/missing required-field rows in the retained population;
6. zero competitive-allocation reconciliation failures;
7. all retained dates are inside 2021–2024;
8. `access_2025 == false` and `access_2026 == false`;
9. raw provider pages and a deterministic canonical retained-row file are preserved with SHA-256 receipts.

If any gate fails, classify `SOURCE_DATA_INSUFFICIENT` or `SOURCE_DATA_FAILURE` as applicable. Do not lower the thresholds, remove a tenor, change the date range or alter required fields under this gate ID.

## Source-stage allowed outputs

Allowed: row counts, per-tenor counts, schema/integrity checks, delta availability counts, equal-delta count, bidder-allocation reconciliation, source SHA-256 receipts.

Forbidden: BTC prices, BTC returns, PnL, PF, win rate, bootstrap of BTC outcomes, year selection by BTC performance, 2025/2026 data, live trading, exchange mutation.

## Next authority

A `SOURCE_DATA_PASS` under this exact gate would authorize only preparation of a separate immutable pre-Discovery authority. It does not itself authorize BTC outcome access.
