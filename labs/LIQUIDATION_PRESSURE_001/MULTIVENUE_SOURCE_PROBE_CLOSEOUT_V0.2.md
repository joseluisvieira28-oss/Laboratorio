# LIQUIDATION-PRESSURE-001 — Multi-Venue Historical Source Route Closeout V0.2

Date: 2026-09-19  
Branch: `liquidation-pressure-tardis-source-v0.2`  
Probe: `LP-MULTIVENUE-SOURCE-PROBE-002`  
Canonical run: `35456934882`  
Artifact ID: `10588118764`  
Artifact digest: `sha256:3bb47b308b0f3b7c63ee7bba93718d43901c50054caeacc2c614926d449a5402`

## Final classification

**MULTIVENUE_HISTORICAL_SOURCE_ROUTE_FEASIBLE**

This is a source/provenance result only. No forward price, continuation/reversal label, return, PnL or strategy metric was opened.

## Frozen sample

Dates: 2021-09-01, 2022-01-01, 2023-01-01, 2024-01-01.

All five prospectively frozen venue routes passed the corrected source-feasibility rule:

- Binance USDT Futures — `BTCUSDT`
- BitMEX — `XBTUSD`
- Deribit — `BTC-PERPETUAL`
- Bybit Derivatives — `BTCUSD` / `BTCUSDT`
- Kraken Futures / Crypto Facilities — `PI_XBTUSD`

Zero-event days are treated correctly as valid source states when the dataset file is addressable and transport/provenance checks pass.

## Source-quality caveats

Passing source availability does **not** mean every venue publishes every liquidation.

- Binance is explicitly known to be censored after 2021-04-27: its forceOrder feed is snapshot order data at a maximum frequency of one push per second.
- Bybit changes collection method inside the historical window: REST polling through 2021-09-20, then WebSocket liquidation channel.
- BitMEX, Deribit and Kraken Futures have no Binance-style Tardis throttling warning pinned in the current source review, but absence of a warning is not proof of perfect event completeness.

No venue may be selected because it showed more liquidation records on the frozen sample dates.

## Scientific consequence

The original historical-liquidation blocker is no longer a blanket **DATA_UNAVAILABLE** blocker.

A reproducible pre-2025, multi-venue historical liquidation route exists. The remaining blocker is **full-history acquisition + source-quality/censoring governance**, not basic historical existence.

Before Discovery:
1. complete source-continuity census without market outcomes;
2. freeze eligible venue basket using provenance/coverage only;
3. define event clustering and cross-venue deduplication;
4. define pressure units that remain valid across contract types;
5. freeze minimum sample gate;
6. only then open a one-shot Discovery.

## Safety

2025/2026 closed. No paid subscription, API key, live trading, exchange mutation, wallet access, main merge or post-outcome tuning was used.
