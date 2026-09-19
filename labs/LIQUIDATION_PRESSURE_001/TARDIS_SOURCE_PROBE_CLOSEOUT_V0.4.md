# LIQUIDATION-PRESSURE-001 — Tardis Historical Source Route Closeout V0.4

Date: 2026-09-19  
Branch: `liquidation-pressure-tardis-source-v0.2`  
Probe: `LP-TARDIS-SOURCE-PROBE-004`  
Canonical run: `35456583001`  
Artifact: `LIQUIDATION_PRESSURE_001_TARDIS_SOURCE_PROBE_V0_4`  
Artifact ID: `10588303171`  
Artifact digest: `sha256:9ab1d60307a31d476077c9574c35f9ef46be98ce0925cecd595e53b7a5dce65c`  
Receipt SHA256: `b72b45d3ce7c99517ea0be911b7d347cf44b72496c40ee372992c99121ea51ee`

## Final classification

**HISTORICAL_LIQUIDATION_SOURCE_ROUTE_FEASIBLE**

This is a source/provenance result only. It is not a continuation/reversal, expectancy, PnL, hit-rate, Sharpe or promotion verdict.

## Preserved lineage

The original `liquidation-pressure-v0.1` closeout remains historically correct for the official/free-data-first routes tested there: no reproducible historical market-wide liquidation archive had been proven.

V0.2 and V0.3 Tardis probes remain preserved as transport failures:
- V0.2 used an unproven grouped dataset symbol and failed HTTP 404.
- V0.3 corrected the symbol to `BTCUSDT` but used the wrong date-path shape and failed HTTP 404.

Neither failure opened market outcomes. V0.4 changed only the URL date segmentation to the documented Tardis dataset path.

## V0.4 evidence

All four prospectively frozen samples returned HTTP 200 with the required normalized liquidation schema:

`exchange, symbol, timestamp, local_timestamp, id, side, price, amount`

BTCUSDT row counts:
- 2021-09-01: **1,461**
- 2022-01-01: **1,052**
- 2023-01-01: **81**
- 2024-01-01: **1,206**

Total across the four feasibility dates: **3,800 historical BTCUSDT liquidation records**.

The receipt preserved per-file compressed SHA-256 digests and first/last event timestamps. No market-price outcome series was loaded.

## Critical source limitation

Tardis states that Binance USDT Futures liquidations are collected from the exchange `forceOrder` stream. Since 2021-04-27, Binance no longer publishes that stream as full realtime liquidation order flow; it publishes snapshot order data at a maximum frequency of one order push per second.

Therefore this source is sufficient to prove **historical observed liquidation-feed feasibility**, but it must **not** be treated as a complete ground-truth census of every liquidation or exact total forced notional during dense cascades.

Any future experiment must explicitly preserve this censoring limitation and may not silently describe the data as complete market-wide liquidation flow.

## Scientific transition

The old state:

`SOURCE_ACCESS_BLOCKED / REPRODUCIBLE_HISTORICAL_MARKETWIDE_LIQUIDATION_ARCHIVE_NOT_PROVEN`

is superseded for this new route by:

`HISTORICAL_LIQUIDATION_SOURCE_ROUTE_FEASIBLE / OUTCOMES_LOCKED`

The next valid transition is **not** Discovery.

Next:
1. source-continuity / coverage census across the frozen pre-2025 period;
2. quantify documented feed censoring and exchange coverage;
3. freeze event clustering and pressure-state definition without forward prices;
4. freeze minimum event/sample gate;
5. only then open one Discovery under a new pre-discovery authority.

## Safety receipt

- market price outcomes opened: FALSE
- forward returns computed: FALSE
- continuation/reversal tested: FALSE
- PnL/performance computed: FALSE
- 2025 accessed: FALSE
- 2026 accessed: FALSE
- paid subscription used: FALSE
- API key used: FALSE
- live trading/exchange mutation/wallet access: FALSE
- merge to main: FALSE
- post-outcome tuning: FALSE
