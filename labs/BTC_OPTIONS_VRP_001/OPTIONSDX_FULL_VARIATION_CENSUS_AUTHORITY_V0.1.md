# BTC-OPTIONS-VRP-001 — optionsDX FULL VARIATION CENSUS AUTHORITY V0.1

Date: 2026-09-27
Branch: `btc-options-vrp-optionsdx-full-census-v0.1`
Parent source lineage: `OVRP-EXEC-FREE-ROUTE-001-SOURCE`

## Purpose

Resolve one remaining public procurement question without opening strategy outcomes:

**Does the public optionsDX BTC Deribit product expose any USD 0 intraday variation (30m / 15m / 5m / minutely), not merely End of Day, anywhere in the visible 2021-06 through 2024-09 catalog?**

## Frozen method

Use only:
- public BTC product page;
- public WooCommerce `wc-ajax=get_variation` endpoint used by the selector itself;
- product id `1527`;
- the exact visible public period/frequency selector cross-product.

Enumerate the full visible cross-product, up to 250 lookups. Do **not** stop at the first zero-price variation.

For every resolved variation record only:
- period;
- quote frequency;
- variation id;
- display price;
- regular display price;
- active / in-stock / purchasable flags.

## Classification

- `OPTIONSDX_FREE_INTRADAY_VARIATION_FOUND` if any USD 0 variation has quote frequency in {30 Minutes, 15 Minutes, 5 Minutes, Minutely}.
- `OPTIONSDX_ZERO_PRICE_EOD_ONLY` if one or more USD 0 variations exist but all are End of Day.
- `OPTIONSDX_NO_ZERO_PRICE_VARIATION_VISIBLE` if all visible variations resolve and none are USD 0.
- `OPTIONSDX_CATALOG_METADATA_PARTIAL` if some but not all visible combinations resolve and no intraday-free route can be proven.
- `OPTIONSDX_CATALOG_ACQUISITION_FAILURE` if no defensible census can be completed.

## Scientific boundary

This is procurement metadata only.

Forbidden:
- add to cart;
- checkout;
- account creation;
- login;
- order creation;
- payment;
- file download;
- opening any option quote payload;
- strategy return/PnL/expectancy/PF/drawdown;
- 2025/2026 strategy access;
- parameter changes;
- live trading;
- exchange mutation;
- merge to main.

Cash spend cap: exactly USD 0.

The result may update source-route feasibility only. It cannot change the positive parent discovery or create an execution-performance verdict.
