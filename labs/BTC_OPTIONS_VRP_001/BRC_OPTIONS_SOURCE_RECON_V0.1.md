# BTC-OPTIONS-VRP-001 — BRC OPTIONS SOURCE RECON V0.1

Date: 2026-09-19
Scope: public-source identity/provenance only
Cash spend: USD 0
User identity submitted: no
Credentials used: no

## Classification

**BRC_OPTIONS_ROUTE_RESEARCH_ACCESS_PLAUSIBLE__CURRENT_ACCESS_IDENTITY_GATED**

This is not a source-data pass.

## Published evidence

The 2023 paper *Pricing Kernels and Risk Premia implied in Bitcoin Options* states that its database contains **8,444,664 Deribit order-book snapshots** collected from **2021-04-01 through 2022-04-01** via Deribit API V2. It explicitly describes high-frequency order-book changes and trades for BTC **options and futures** and states that the database is available through the Blockchain Research Center.

A second published study using BRC BTC option data reports using the data from 2021-04-13 through 2022-03-07 at a 20-minute research frequency.

## Public code evidence

The public QuantLet repository `QuantLet/BitcoinOptions` contains `src/brc.py`.

The code:
- uses a Mongo collection named `deribit_orderbooks`;
- reads `best_bid_price`, `best_ask_price`, `underlying_price`, `index_price`, `mark_iv`, `instrument_name` and timestamps;
- computes option instrument prices from bid/ask;
- confirms the research implementation was built around actual order-book snapshots rather than trades alone.

The repository also contains obsolete connection scaffolding. It must **not** be treated as present authorization to connect to any BRC host. No connection attempt is authorized or performed.

## Current BRC public catalogue discrepancy

The current BRC public request-data page prominently describes:
- a Deribit BTC **futures** order-book dataset since 03/2020;
- a separate generic `Deribit LOB` description.

The public catalogue does not clearly identify the historical BTC **options** subset described by the 2023 publications.

BRC's public site says data/code material is available upon request or query and frames access around its research community/member workflow. Therefore the historical options dataset's current availability to a new requester is not proven from the public surface.

## Adjudication

Do not:
- attempt the obsolete Mongo host/username from public research code;
- guess credentials;
- infer that the current futures catalogue automatically includes options;
- submit the user's identity/contact details without a separate action;
- open strategy outcomes.

A future BRC action is justified only as an **access/identity request** asking whether the exact 2021-04-01 to 2022-04-01 BTC options order-book dataset cited in DOI 10.3390/risks11050085 remains available, under what research-access terms, and in what current format.

Until that is answered, BRC remains a potentially valuable free/academic route but not an executable source.
