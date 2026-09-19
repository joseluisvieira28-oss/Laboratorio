# BTC-OPTIONS-VRP-001 — optionsDX ZERO-PRICE CATALOG TECHNICAL AMENDMENT V0.1A

Date: 2026-09-19
Parent probe: `OVRP-OPTIONSDX-ZERO-PRICE-CATALOG-001`
First run: `35458091674`

## Reason

The first run reached both the public product page and the public WooCommerce Store API without any cart, checkout, account or payment action.

The Store API returned 200 variation identifiers but did not expose numeric variation prices in the product-level response. The original parser therefore produced an empty `distinct_display_prices` set while incorrectly classifying the result as `OPTIONSDX_NO_ZERO_PRICE_VARIATION_VISIBLE`.

Because the frozen scientific/procurement question is specifically whether an identifiable full-data variation is publicly priced at exactly USD 0.00, an absence of price metadata cannot adjudicate that question.

## Preserved first-run state

Run `35458091674` is retained as:

`NON_ADJUDICATIVE_PRODUCT_LEVEL_METADATA_RUN`

It proves only that the public Store API exposes a variation catalogue. It does not prove that no zero-price variation exists.

## Authorized technical correction only

1. Resolve the public product ID from the same Store API response.
2. Query the public read-only Store API variation-detail endpoint for that same product.
3. Read only public variation attributes and price metadata.
4. Do not add to cart, checkout, create an account, download a paid dataset, or submit user information.
5. Keep cash-spend cap at USD 0.
6. Keep all outcome/trading prohibitions unchanged.

The corrected V0.1A run may adjudicate only the frozen zero-price catalogue question.
