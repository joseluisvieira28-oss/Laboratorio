# Cross-venue source adjudication — outcome blind

These are bounded official-domain leads, not a complete Bybit/OKX historical universe. No market values fetched.

## Binance examples
- e71da970ed29453c96018af9bf107311: claimed publication 2025-11-25 02:01; planned start 2025-11-28 06:30 UTC, approximately one hour implementation. Existing exposure is affected; VFY/BAS/etc first-tier maintenance margin moves 1.50% to 2.00%, leverage 50x to 40x. This is real tightening, conditional on customer buffers; no evidence of unconditional closure. CMS reports version 1, lastUpdateTime 0. These fields do not independently prove historical immutable content.
- 4d5f22d4048345d4b7cbb7920d2af2ee: claimed publication 2025-04-01 07:32; effective start 10:30 UTC. Existing positions affected; quantified tier changes. Historical pre-effective body remains unverified.
- aa735cd2d8bd4e7bb092179cf086e486: preannounced 2024-05-28 adjustment explicitly excludes existing positions. Reject mechanism for this family.
- 0806a835368b409e8d5ebd84d9fdc4ed: 2024-06-10 collateral reductions, including LINK/AAVE 90% to 80%, FLUX/PYR/WOO 70% to 40%. Customers can top up collateral. The collateral asset does not identify which derivatives exposure an account finances; no affected-token-perpetual OI binding may be presumed.
- 14d6edbcf4254d86aeb5e9cfbceb2db6: current source explicitly reports October 22 amendment to effective dates. Cannot use initial publication timestamp as timestamp of knowledge of the current deadline.
- ea3fdf1c24c048dba00d8083f9248fd6: current source reports September 2 amendment to previous leverage/margin tiers. Original/current rules must not be conflated.

Canonical URLs: https://www.binance.com/en/support/announcement/detail/{article_code}

## Bybit
https://announcements.bybit.com/en/article/risk-limit-adjustment-for-xnyusdt-perpetual-contract-blt09ebc41170874c39/
The search renderer exposes the heading and December 5, 2025 date, but no operative rule body/deadline. Direct HTTP 200 returns 195-byte Site Unavailable HTML. HTTP status alone is not successful source recovery. XION/ID/PIGGY announcements are leads only, not accepted events.
https://www.bybit.com/en/help-center/article/Understanding-the-Adjustment-and-Impact-of-the-New-Margin-Calculation
Current help page updated June 18, 2026. Describes gradual rollout from September 2, 2025, with exposure-dependent effects. Not a contemporaneous immutable notice with an exact universal deadline. Generic API OI schema exists: https://bybit-exchange.github.io/docs/v5/market/open-interest ; no event-window data fetched or historical coverage claimed.

## OKX
https://www.okx.com/en-eu/help/okx-to-adjust-position-tiers-of-certain-perpetuals-20251117
Published November 17; implementation November 19, 2025 06:00–10:00 UTC. Mixed loosening/tightening across instruments: do not classify an entire headline as forced contraction. Four-hour implementation interval does not provide an exact per-contract deadline.
https://www.okx.com/en-gb/help/okx-to-adjust-position-tiers-of-margins-and-discount-rates-20250409
Contains quantified old/new changes and acknowledges customers can increase margins or close positions to avoid liquidation. Collateral/margin-to-specific-perpetual OI binding remains missing. A later official postponement is a separate source that must supersede the original when applicable:
https://www.okx.com/en-eu/help/okx-to-postpone-adjusting-margin-position-tiers-for-usdt
No full historical same-venue OI/basis/funding coverage demonstrated. No cross-venue substitution using Binance OI permitted.

## Retrieval/search limitations
Search service system2 produced official leads; the system1 verification batch returned irrelevant material and was excluded from evidence. Current official dates are provisional historical claims, not recovered pre-effective bodies. Wayback CDX transport failure is not evidence that captures do not exist. Searches do not establish exhaustive sample absence.
