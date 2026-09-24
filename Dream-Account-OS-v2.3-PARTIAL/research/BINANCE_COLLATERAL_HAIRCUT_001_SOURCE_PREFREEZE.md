# BINANCE-COLLATERAL-HAIRCUT-001 — SOURCE CENSUS PRE-FREEZE

Date frozen: 2026-09-24
Status: SOURCE_PRE_FROZEN
Governance: CRYPTO-LAB-GOVERNANCE-V4.0-DEATH-FROZEN
Primary family: ACCESS
Secondary family: EVENT

## Mechanism

A change in the Portfolio Margin collateral ratio changes how much margin value Binance assigns to an asset.

- ratio decrease = tighter collateral capacity / larger haircut;
- ratio increase = looser collateral capacity / smaller haircut.

This is materially different from:
- spot listing;
- perpetual launch;
- margin borrowability;
- delisting.

## Frozen source window

Official Binance announcements only:
2024-01-01 through 2024-12-31 UTC.

Canonical enumeration:
- immutable Binance Announcements Telegram index for article discovery;
- canonical Binance Support article-detail endpoint for identity, release time and body;
- no web-search result is an event authority.

Candidate article must explicitly reference:
- "collateral ratio";
- "Portfolio Margin".

## Event extraction

For each canonical article:
- retain official article code/title/release timestamp;
- parse the Portfolio Margin table whose columns contain:
  - asset;
  - collateral ratio before;
  - collateral ratio after;
- parse exact announced effective UTC timestamp;
- require release time < effective time;
- compute delta percentage points = after - before.

An article may contribute multiple asset-events, but scientific independence is article/effective-time cluster level.

## Source gate

PASS only if all are true:
- >=4 independent article/effective-time clusters;
- >=20 parsed asset-events;
- >=15 unique assets;
- >=5 tightening events (delta < 0);
- >=5 loosening events (delta > 0);
- every retained event has numeric before/after ratios and exact effective UTC timestamp;
- every retained article was published before effective time;
- four frozen positive-control articles are recovered:
  - 0806a835368b409e8d5ebd84d9fdc4ed
  - 3f0978bcf69643aeb29424d45c9b810c
  - b9fad723c9c64240801d0e11dd77faa8
  - 51bb9a7a59d2472cbd0c2b3ff38fe9bd

PASS:
`BINANCE_COLLATERAL_HAIRCUT_SOURCE_PASS`

Otherwise:
`SOURCE_INSUFFICIENT`, `PROVENANCE_FAILURE`, or `SOURCE_ACQUISITION_TECHNICAL_FAILURE`.

## Firewall

No spot prices.
No BTC prices.
No returns.
No PnL.
No 2025 or 2026 announcement enumeration.
No authenticated API.
No account data.
No exchange mutation.
No live trading.
No merge to main.
