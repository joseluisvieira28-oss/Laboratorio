# BTC-OPTIONS-VRP-001 — FREE ROUTE STAGE C PUBLIC-DATA PROBE V0.1

Date: 2026-09-19
Scope: source-only / outcome-blind / zero-cash public-data reconnaissance

## New direct public evidence

### 1. bottama/Deribit-Option-Data — historical BBO schema witness

A public GitHub CSV was read directly from:
`bottama/Deribit-Option-Data/csv_files/btc_option_data.csv`

Observed file facts:
- rows: 976
- timestamped rows: 976
- minimum timestamp: 2021-02-11T18:37:05.262Z
- maximum timestamp: 2021-02-11T18:44:14.256Z
- observed span: about 7 minutes
- columns: 32
- includes `best_bid_price`, `best_bid_amount`, `best_ask_price`, `best_ask_amount`, full `bids` / `asks`, mark IV, Greeks, OI, index and underlying price.

Adjudication:
`FREE_SCHEMA_WITNESS_ONLY__INSUFFICIENT_TEMPORAL_COVERAGE`

This is useful as a free independent schema/example witness and confirms that historical Deribit public-API option BBO snapshots were captured by third parties before our parent window. It is nowhere near the required temporal coverage. No license was established by the current repo probe, so the file is not imported/copied into the Crypto Lab.

### 2. schepal/crypto_gamma_exposure — historical BBO schema witness

Public CSV:
`schepal/crypto_gamma_exposure/data/options_data.csv`

Observed file facts:
- rows: 358
- timestamped rows: 358
- minimum timestamp: 2020-09-12T23:05:52.543Z
- maximum timestamp: 2020-09-12T23:08:56.948Z
- observed span: about 3 minutes
- includes best bid/ask price+amount and full order-book arrays.

Adjudication:
`FREE_SCHEMA_WITNESS_ONLY__OUTSIDE_TARGET_PERIOD__INSUFFICIENT_TEMPORAL_COVERAGE`

No license was established in this probe, so no dataset bytes are imported into our repository.

### 3. crypto-data.io free one-day sample

Public search surface states:
- one day of historical Deribit futures/options data is available free;
- sample license is CC0 1.0 Universal;
- collection was by polling Deribit API every 5 minutes since July 2023;
- full July-2023-to-current dataset is quote-only/commercial by request.

The current site route redirects and the sample object/schema could not be recovered automatically in this environment.

Adjudication:
`FREE_ONE_DAY_SAMPLE_ROUTE_DISCOVERED__PAYLOAD_PENDING`

This route is now ahead of paid providers for sample validation but behind the already-documented free 2024H1 Cryptarbitrage file for useful historical breadth.

## BRC caution

The published BTC-options study does establish 8,444,664 Deribit order-book snapshots from 2021-04-01 through 2022-04-01, but it also states that instruments were polled successively rather than simultaneously because of API rate limits. This does not invalidate the dataset as research evidence, but simultaneity/execution semantics must be examined before using it for any future multi-leg executable MVE.

The current BRC public catalogue mainly advertises BTC Futures order-book data and requires a free account plus accreditation for member datasets. Do not assume the paper's options subset is currently downloadable until verified after user-controlled onboarding.

## Updated zero-cash priority

1. Recover Cryptarbitrage 2024H1 parquet direct object.
2. Recover crypto-data.io free historical day and inspect its BBO fields/license receipt.
3. Recover optionsDX public BTC sample payload and inspect exact timestamps/BBO sizes.
4. BRC member route only if user elects to create/accredit a research account; verify options dataset identity before download.
5. CoinAPI signup-credit probe only with user-owned credential and zero paid overage.
6. Commercial route only after a minimal bill of materials is frozen.

## No-outcome receipt

No strategy returns, PnL, expectancy, PF, future realized variance, protected-period outcome or parameter optimization was opened during Stage C.
