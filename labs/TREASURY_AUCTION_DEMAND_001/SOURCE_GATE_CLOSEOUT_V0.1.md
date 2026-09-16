# TREASURY-AUCTION-DEMAND-001 — SOURCE GATE CLOSEOUT V0.1

Date: 2026-09-16

## Canonical execution

- Lab: `TREASURY-AUCTION-DEMAND-001`
- Gate: `TAD-COUPON-SOURCE-001`
- GitHub Actions run: `35128643997`
- Job: `104903845684`
- Tested head: `4262f34b460f9ca29af100728372ef0558aadd1a`
- Evidence artifact ID: `10459379931`
- Artifact ZIP SHA-256: `d6968b44a09314e437e92b04ab338942273833286b184d13f11c063749548159`
- Canonical retained-row SHA-256: `ab2695123b04c6e320bda23e5496b1dcfadabec8c6784211a10407ac87499892`

## Classification

`SOURCE_DATA_PASS`

This is not an economic edge verdict. BTC market values, returns and PnL were not opened.

## Frozen-gate result

All prospectively frozen source gates passed:

- retained nominal coupon auctions: **337** >= 300;
- comparable same-tenor delta rows: **330** >= 280;
- each frozen tenor >= 40: PASS;
- 2-Year: 48;
- 3-Year: 48;
- 5-Year: 47;
- 7-Year: 49;
- 10-Year: 48;
- 20-Year: 49;
- 30-Year: 48;
- duplicate `(auction_date, cusip)` identities: **0**;
- invalid/missing retained rows: **0**;
- competitive bidder-allocation reconciliation failures: **0**;
- provider rows outside frozen 2021–2024 filter: **0**;
- protected-period access: `2025=false`, `2026=false`;
- raw pages + deterministic canonical file + SHA receipts: PASS.

Source-only sign balance for the prospectively defined same-tenor bid-to-cover change:

- positive delta: **165**;
- negative delta: **159**;
- exactly zero: **6**.

These counts were not selected or tuned against BTC outcomes.

## Provenance

Official U.S. Treasury Fiscal Data endpoint:
`/v1/accounting/od/auctions_query`

The run preserved 17 raw JSON pages covering exactly `auction_date:gte:2021-01-01` through `auction_date:lte:2024-12-31`, plus the canonical retained-row file and manifests.

## Governance

`access_2025=false` / `access_2026=false` / `btc_market_values_opened=false` / `btc_returns_opened=false` / `pnl_opened=false` / `live_trading=false` / `exchange_mutation=false`.

`SOURCE_DATA_PASS` authorizes preparation of a separate immutable pre-Discovery authority only. It does not itself open BTC outcomes.
