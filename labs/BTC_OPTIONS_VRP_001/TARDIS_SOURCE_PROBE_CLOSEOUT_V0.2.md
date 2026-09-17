# BTC-OPTIONS-VRP-001 — Tardis Source Probe Closeout V0.2

Date: 2026-09-17
Branch: `btc-options-vrp-tardis-source-probe-v0.1`
Probe ID: `OVRP-EXEC-SOURCE-TARDIS-PROBE-002`
Canonical run: `35274543014`
Canonical artifact: `BTC_OPTIONS_VRP_001_TARDIS_SOURCE_PROBE_V0_2`
Artifact ID: `10520101272`
Artifact ZIP digest: `sha256:358652fdb6701ce89062d5e4f2b7e1227a7c764521b81835378c45bfc95a28f7`
Receipt SHA256: `a8d56d306cc8ee95a048318587c22b962d0295a73cb3e73a022c6dce5ee9d7fa`

## Final classification

**PAID_SOURCE_ROUTE_FEASIBLE**

This is a source-feasibility result only. It is not a strategy-performance result and does not authorize paid access, execution, 2025/2026 access, live trading or promotion.

## Preserved lineage

The original execution MVE `OVRP-EXEC-ATM30-7D-STATICDELTA-001` remains closed as `EXECUTION_DATA_LIQUIDITY_INSUFFICIENT`: 19 executable episodes versus the frozen minimum 120 using direction-matched Deribit public trade prints. No performance verdict was opened under that MVE.

Tardis probe V0.1 run `35273908796` remains recorded as `SOURCE_ROUTE_SCHEMA_INSUFFICIENT`. The subsequent schema diagnostic `35274231199` proved the failure was caused by an incompatible free-sample calendar: 2021-06-01 had zero contracts in the frozen 25–35 DTE band. The V0.1 result was not rewritten. V0.2 changed only the free sample dates, per `TARDIS_SOURCE_PROBE_V0_1_ERRATUM.md`.

## V0.2 evidence

The corrected probe used January 1 samples in 2021, 2022, 2023 and 2024, with the same frozen 25–35 DTE requirement, same-strike call+put requirement, option-chain BBO requirement and dedicated quotes BBO requirement.

All four dates passed:

- 2021-01-01: `BTC-29JAN21-28000-C/P`, 28 DTE; both quote BBO legs proved.
- 2022-01-01: `BTC-28JAN22-42000-C/P`, 27 DTE; both quote BBO legs proved.
- 2023-01-01: `BTC-27JAN23-20000-C/P`, 26 DTE; both quote BBO legs proved.
- 2024-01-01: `BTC-26JAN24-35000-C/P`, 25 DTE; both quote BBO legs proved.

The source schema exposed option identity, timestamp, type, strike, expiration, open interest, bid/ask prices and sizes, IV fields, mark data, underlying price and Greeks. The dedicated `quotes` samples supplied nonempty historical BBO for both selected option legs.

## Safety receipt

- API key used: false
- paid subscription used: false
- returns computed: false
- strategy PnL computed: false
- PF/drawdown/expectancy computed: false
- 2025 accessed: false
- 2026 accessed: false
- exchange mutation/live trading/wallet access: false

## Adjudication

A genuinely higher-quality historical quote route exists and is structurally capable of supporting a new execution MVE. Full historical access is commercial/paid, so no execution backtest is authorized or possible under this probe alone.

Any future executable study must use a **new MVE ID and new prospective authority**. The old trade-print MVE may not be rescued or rewritten. Paid access must be separately authorized/provided before any full-history request or performance computation.
