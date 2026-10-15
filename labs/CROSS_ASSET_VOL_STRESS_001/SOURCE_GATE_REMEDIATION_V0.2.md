# CROSS-ASSET-VOL-STRESS-001 — SOURCE GATE REMEDIATION V0.2

Pre-outcome transport/parser remediation only.

## V0.1 status
Run 35059979158 failed before any BTC/outcome access because the current Cboe annual page is a client-rendered shell and the frozen parser could not find the VX table in initial HTML. This is `TECHNICAL_FAILURE_PREOUTCOME`, not a source verdict and not an edge verdict.

## Outcome-blind route discovery
A separate static-client diagnostic opened only the Cboe 2018 page and its JavaScript bundles. It made no settlement-data endpoint request and no BTC request. It recovered the official Cboe frontend endpoint contract:

`https://www-api.cboe.com/us/futures/market_statistics/final_settlement_prices/values/futures/?year=<YYYY>`

The frontend response contract identifies product objects with `product`, `monthly_settlement_prices`, and `weekly_settlement_prices`; settlement records expose `symbol_name`, `expire_date`, `price`, and `calculation_method`.

## V0.2 changes
Only source transport/parser changes. Scientific source scope and all gates remain unchanged.

For each and only each year 2018, 2019, 2020, 2021, 2022, 2023, 2024:
- request exactly the official `www-api.cboe.com` endpoint above with `year=<YYYY>`;
- require response year binding to match the requested year if the provider exposes `selectedYear` or equivalent;
- select exactly the product whose provider-native product label is `VX - Cboe Volatility Index (VX) Futures` or an unambiguous exact VX futures equivalent;
- combine its monthly and weekly final-settlement records;
- parse `expire_date`, `symbol_name`, `price`, and `calculation_method`;
- preserve every raw JSON response byte-for-byte with SHA-256.

No CSV fallback, search-engine scrape, VIX spot series, VXM, variance product, or third-party source is authorized.

## Unchanged PASS gates
- finite positive settlement values;
- each source date belongs to its requested year;
- conflicting values on one settlement date fail closed;
- identical same-date duplicates may be canonicalized and counted;
- >=45 unique canonical VX settlement dates per year;
- >=320 unique canonical settlement dates total across 2018–2024;
- no request for 2025 or 2026;
- no BTC market data, returns, PnL, signal performance, or outcome evaluation.

A V0.2 PASS authorizes only prospective source binding / Discovery preparation under the already frozen lab authority.