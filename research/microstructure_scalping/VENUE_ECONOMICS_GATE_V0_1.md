# VENUE ECONOMICS GATE V0.1

Date: 2026-09-26
Purpose: execution-cost feasibility overlay; no strategy retuning.

## Current published base/reference rates

### MEXC Futures API
Official announcement effective 2026-06-01:
- maker: 0.06% = 6 bps / side
- taker: 0.08% = 8 bps / side
- maker/maker round trip: 12 bps
- taker/taker round trip: 16 bps

API rates explicitly override web/app promotional rates.

### Bybit Perpetual & Futures — VIP 0
Official Bybit fee table, updated 2026-07-30:
- maker: 0.0200% = 2 bps / side
- taker: 0.0550% = 5.5 bps / side
- maker/maker round trip: 4 bps
- taker/taker round trip: 11 bps

Bybit notes actual rates can vary by region/account and should be checked in My Fee Rate.

### Binance USD-M Futures — regular reference
Official Binance fee-calculation article updated 2026-05-01 gives regular-user example:
- maker: 0.02%
- taker: 0.05%
- maker/maker reference round trip: 4 bps
- taker/taker reference round trip: 10 bps
Actual account rates and discounts can vary.

### OKX futures — lv1 reference
Official OKX article updated 2026-08-26:
- maker: 0.02%
- taker: 0.05%
- maker/maker reference round trip: 4 bps
- taker/taker reference round trip: 10 bps

### Hyperliquid perps — base tier
Official fee docs:
- maker: 0.015% = 1.5 bps / side
- taker: 0.045% = 4.5 bps / side
- maker/maker base round trip: 3 bps
- taker/taker base round trip: 9 bps
Higher-volume/staking tiers can differ.

## Scientific consequence
The current MEXC API fee structure is structurally hostile to the sub-10-bps mean signals observed in this lab.

Alternative venue economics may change feasibility, but venue transfer is NOT assumed.
Every candidate must be revalidated using venue-appropriate executable data and fill assumptions.

Official references:
- https://www.mexc.com/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742
- https://www.bybit.com/en/help-center/article/Trading-Fee-Structure
- https://www.binance.com/en-NZ/support/faq/detail/360033544231
- https://www.okx.com/en-eu/help/how-to-calculate-the-contract-transaction-fee
- https://hyperliquid.gitbook.io/hyperliquid-docs/trading/fees
