# BTC-OPTIONS-VRP-001 — FREE ROUTE STAGE C RECEIPT V0.1

Date: 2026-09-19
Branch: `btc-options-vrp-free-route-attack-v0.1`

## Result 1 — free prospective BBO route is operational

Canonical one-shot run: `35458192591`  
Artifact: `10589675263`  
Classification: **PUBLIC_FORWARD_BBO_SOURCE_CAPTURE_PASS**

Using only unauthenticated Deribit public endpoints, the frozen source-only collector:

- selected 72 BTC option instruments inside the broad 20–45 DTE / +/-25% strike-distance envelope;
- captured BBO source data for all 72;
- recorded zero instrument failures;
- captured the BTC-PERPETUAL reference book;
- used no authentication, API key, wallet or order endpoint;
- computed no returns or PnL.

Raw one-shot source artifact:
- 48,110 bytes;
- SHA256 `6e3230833b00d16c3b3111e7f5759e1387509102f17e9e7e75b3cbf034d4ea3c`.

This proves we can build our own prospective BBO archive at zero vendor cost. It is not a strategy result.

## Result 2 — optionsDX public sample is rich but fails the exact sample gate

Corrected sample run `35457977533` retrieved 94,066 rows with complete BBO prices and sizes across 458 instruments on 2021-06-01, but had zero rows in the pre-frozen 25–35 DTE band. Exact probe classification: **OPTIONSDX_FREE_SAMPLE_SCHEMA_INSUFFICIENT**.

Do not rescue that probe.

## Result 3 — a zero-price optionsDX full-data variation exists

Public procurement run `35458248379` classified **OPTIONSDX_ZERO_PRICE_VARIATION_FOUND**:

`2021-06 / End of Day / variation 1570 / USD 0.00`.

No cart or checkout was used. optionsDX's public FAQ states that free datasets are delivered after checkout, with no billing information requested. Therefore direct anonymous acquisition is not yet proven; the likely remaining gate is a zero-dollar checkout/account workflow outside the current no-side-effect authority.

## Result 4 — BRC remains scientifically interesting but access identity is unresolved

Published research states that the BRC database contains 8,444,664 Deribit order-book snapshots from 2021-04-01 through 2022-04-01, with options and futures captured from `public/get_order_book` and trade endpoints.

The current public BRC catalogue prominently describes BTC futures/order-book data and a generic Deribit LOB feed. It does not clearly expose the exact options subset from the publication on the public catalogue surface.

Do not assume current downloadable options access until that identity is proven.

## Result 5 — Cryptarbitrage free 2024H1 dataset exists but direct object remains unrecovered

Deribit Insights links to the author's X post and explicitly states that the linked parquet contains hourly snapshots of all Deribit BTC options from 2024-01-13 through 2024-07-27. Public search confirms the dataset description, but the direct parquet object URL is not exposed by the accessible X page/search surface.

Route remains worth pursuing because it is zero-cost and closer to the old MVE's intraday execution needs than EOD data.

## Priority after Stage C

1. Continue recovering the Cryptarbitrage direct parquet object without requiring user identity.
2. Continue public BRC dataset-identity research; stop before accreditation/user submission.
3. Keep optionsDX zero-price EOD as a validated free fallback. A free checkout would require separate user action because the file is delivered through an orders/account flow.
4. Keep CoinAPI credential probe dormant until the anonymous/public routes above are exhausted.
5. Keep Tardis commercial access last. No paid decision until an exact minimal bill of materials and exact cost are produced.
