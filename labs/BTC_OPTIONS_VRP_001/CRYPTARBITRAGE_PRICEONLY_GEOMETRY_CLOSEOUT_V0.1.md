# BTC-OPTIONS-VRP-001 — CRYPTARBITRAGE PRICE-ONLY GEOMETRY CLOSEOUT V0.1

Date: 2026-09-19
Diagnostic: `OVRP-CRYPTARBITRAGE-PRICEONLY-GEOMETRY-001`
Canonical run: `35469345729`

## Final classification

**PRICE_ONLY_GEOMETRY_SPARSE_EXECUTION_SIZE_BLOCKED**

The exact free Cryptarbitrage parquet is a real and substantial historical Deribit options dataset:

- 4,498,832 rows;
- 3,793,682 rows with positive bid/ask prices;
- 156,536 positive-BBO rows inside 25–35 DTE;
- 1,477 distinct UTC hours inside 25–35 DTE;
- 68 distinct UTC dates inside 25–35 DTE;
- 72,588 same-snapshot/same-expiry/same-strike call+put pair keys;
- open-interest and volume fields non-null on all 156,536 in-band rows;
- bid-size column absent;
- ask-size column absent.

Frozen rich-geometry gate required at least 120 distinct UTC hours, 90 distinct UTC dates, and 120 paired call+put snapshot keys. The file passes the hour and paired-key requirements by a large margin but fails the 90-date breadth requirement with 68 dates.

## Scientific interpretation

This route contains rich historical price-only structure but remains insufficient for an executable BBO-source claim because:
1. quote sizes are absent; and
2. the prospectively frozen date-breadth gate is not met.

The exact execution-source failure remains terminal and is not reopened.

The parquet may still support future source-only market-structure research that does not require executable quote sizes, but it cannot be used to rescue the closed Deribit execution MVE or to justify a promotion.

No returns, realized variance, VRP, PnL, PF, protected-period outcome, live trading, wallet access, exchange mutation, or merge to main was opened.
