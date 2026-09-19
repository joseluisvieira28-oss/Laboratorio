# BTC-OPTIONS-VRP-001 — optionsDX ZERO-PRICE VARIATION LOOKUP AMENDMENT V0.1B

Date: 2026-09-19
Parent probe: `OVRP-OPTIONSDX-ZERO-PRICE-CATALOG-001`
V0.1A run: `35458175209`

## Reason

The public WooCommerce Store API product response exposed product ID 1527 and 200 variation references, but the attempted read-only variation-detail endpoint returned HTTP 404 and exposed no numeric price metadata.

The frozen procurement question therefore remains unresolved: the public product page displays a USD 0–50 range, but we do not yet know which exact period/frequency variation, if any, is priced at USD 0.

## Authorized technical/procurement lookup

Use only the same public product page and WooCommerce's public `wc-ajax=get_variation` lookup used by the product selector itself.

Permitted:
- parse public period/frequency selector values;
- submit only product ID plus selector attributes to the public variation-lookup endpoint;
- record variation ID, selector attributes and public display/regular price;
- stop immediately if a USD 0 variation is found, otherwise enumerate at most the visible selector cross-product;
- conservative request pacing.

Forbidden:
- add-to-cart;
- checkout;
- account creation/login;
- download of any paid product;
- payment method submission;
- purchase/order creation;
- strategy data/outcomes/returns/PnL;
- any 2025/2026 strategy access or live trading.

Cash-spend cap remains exactly USD 0.

V0.1 and V0.1A remain preserved. This amendment does not alter the target question; it only uses the public variation lookup required to resolve product-level metadata that the Store API did not expose.
