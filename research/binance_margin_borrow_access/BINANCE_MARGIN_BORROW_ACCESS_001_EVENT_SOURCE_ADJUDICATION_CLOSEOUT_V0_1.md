# BINANCE-MARGIN-BORROW-ACCESS-001 — EVENT SOURCE ADJUDICATION CLOSEOUT V0.1

Date: 2026-09-17  
Verdict: **EVENT_SOURCE_ADJUDICATION_PASS**  
Branch: `binance-margin-borrow-access-v0.1`

## Scope

This closeout adjudicates source/provenance only for the mechanism frozen before outcomes: relaxation of short-sale/hedging constraints when an asset that was already trading on Binance Spot becomes newly borrowable on Binance Cross Margin.

It is **not** an economic-performance result, edge claim, profitability result or executable-strategy approval.

## Upstream gates

### Source census

- `SOURCE_CENSUS_PASS`
- canonical run `35243636150`
- 232 / 232 relevant/control Binance Support articles hydrated
- 69 structural `Cross Margin` + `borrowable asset` articles
- 2023 and 2024 coverage

### Event parser V0.1.1

- canonical run `35262879137`
- canonical parser artifact id `10516370001`
- artifact digest `sha256:92574b823f9c9ea8ec38c46e6d7d5a27312adf781a64cdcdeba173e65b5f3a0f`
- 69 / 69 structural articles reconciled
- 54 `ADD`
- 6 `REMOVE`
- 9 `OTHER`
- 100 asset-event mentions in the 54 clean ADD articles
- no invalid ADD

The stricter V0.1.1 semantics prospectively excluded cases that did not explicitly prove Cross-Margin borrowing and one open-ended asset list. No market outcomes were used in those exclusions.

### Prior-Spot proof

- canonical run `35269000941`
- `PRIOR_SPOT_PRIMARY_PASS`
- 100 asset-event rows
- 96 `PRIOR_SPOT_ARCHIVE_PASS`
- 4 prospectively excluded `ACCESS_CONFOUND`
- 0 unresolved
- proved years 2023 and 2024
- canonical artifact id `10517374109`
- artifact digest `sha256:bb966915fd7175e7f7b92a2918bb4bd0722e7b3ebd90345df6f07d6a01fd12ca`

The clean research universe entering any later Discovery is therefore **96 asset-events**, not necessarily 96 unique assets. Event/article clustering and repeat assets must be preserved in later inference.

### Execution-cost provenance

- classification: **CREDENTIAL_BOUND**
- legitimate historical Binance interest-rate route exists but is authenticated `USER_DATA`
- no credentials or account data were used
- no historical borrow-rate/inventory values were opened
- no current-value substitution was allowed

## Verdict logic

All required event identity, direction, asset, confound and prior-Spot provenance requirements passed. Execution-cost provenance is legitimately classified `CREDENTIAL_BOUND`, which the frozen authority explicitly allows to proceed only to an explicitly non-executable research Discovery.

Therefore:

**EVENT_SOURCE_ADJUDICATION_PASS**

## Safety / prohibition carry-forward

This pass does not authorize live trading, orders, wallets, exchange mutation, alerts/webhooks, authenticated Binance access, 2025/2026 scientific data, or any claim of after-cost profitability.

It authorizes only creation and freezing of a separate Discovery protocol before opening market outcomes.
