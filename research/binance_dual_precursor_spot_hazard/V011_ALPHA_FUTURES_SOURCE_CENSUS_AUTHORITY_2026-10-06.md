# DUAL PRECURSOR V0.1 — ALPHA/FUTURES SOURCE CENSUS AUTHORITY
Date: 2026-10-06
Status: SOURCE-ONLY / BEFORE SPOT OUTCOME INSPECTION

## Purpose
Establish the 2025 outcome-independent source universe required by the existing V0.1 freeze before any later Binance Spot-listing outcome is classified.

## Alpha authority
Use only the official public Binance Alpha token-list endpoint already source-proven in run 37365852644:
GET /bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list

For V0.1 source census:
- listingTime is treated as the defensible public Alpha-presence timestamp supplied by the official Alpha endpoint;
- retain rows whose listingTime is in calendar year 2025 UTC;
- preserve alphaId, tokenId, symbol, name, chainId, chainName, contractAddress, listingTime and source-status metadata;
- do not use price/liquidity/market-cap fields;
- do not include/exclude based on later Spot listing.

If multiple 2025 Alpha identities share the same ticker and cannot be resolved against a Futures launch by contract/project evidence, that ticker is identity-ambiguous and cannot become a DUAL observation.

## Futures authority
Use official public Binance CMS Futures catalog metadata and article detail only.
Scan 2025 articles whose title/body establishes launch of a USDⓈ-M perpetual contract.
Preserve official article code, releaseDate and contract symbol.
No market prices/returns are inspected.

For a symbol with exactly one Alpha identity:
T_DUAL_SOURCE = max(Alpha listingTime, first official Binance Futures perpetual announcement releaseDate).

This is source construction only. It does NOT yet test whether Spot was already listed at T_DUAL and does NOT inspect whether Spot listed afterward.

## Gate from this stage
Report:
- number of 2025 Alpha identities;
- duplicate/ambiguous Alpha ticker count;
- number of 2025 official Futures launch symbols;
- number of exact ticker joins;
- number of exact joins with T_DUAL in 2025;
- unresolved identities.

If exact outcome-independent DUAL candidates <12, the frozen primary discovery cannot meet its minimum and V0.1 is SOURCE_BLOCKED/INSUFFICIENT_DUAL_SOURCE without opening Spot outcomes.

If >=12, freeze the exact Alpha/Futures source universe before binding/opening Spot-list outcomes.

## Governance
2026 outcome validation remains CLOSED.
No Spot outcome classification in this source census.
No market returns.
No private/authenticated endpoints.
No trading/orders/accounts/wallets/exchange mutation.
No main merge.
