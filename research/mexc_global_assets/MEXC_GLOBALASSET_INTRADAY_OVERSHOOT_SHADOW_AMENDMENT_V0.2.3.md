# MEXC GLOBAL-ASSET INTRADAY OVERSHOOT — SHADOW TECHNICAL AMENDMENT V0.2.3

Date: 2026-10-05  
Branch: `mexc-globalasset-intraday-overshoot-shadow-v0.2.3-remediation-2026-10-05`  
Parent scientific authority: `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_FREEZE_V0.2.md`  
Parent transport authority: `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_AMENDMENT_V0.2.2.md`  
Status: TECHNICAL REMEDIATION ONLY — SCIENCE UNCHANGED

## Defect found

The V0.2.2 collector referenced `threading` and `ws_connect` inside `BinanceKlineCache` but did not import them.

The existing self-test compiled the module and separately probed the Binance WebSocket transport, but did not instantiate `BinanceKlineCache`; therefore the runtime NameError path was not exercised.

No valid forward economic outcome was opened to identify or fix this defect.

## Correction

Only runtime plumbing is changed:

- add `import threading`;
- add `from websockets.sync.client import connect as ws_connect`;
- strengthen the self-test so it imports the collector, verifies `ws_connect` is callable, instantiates the frozen Binance cache, requires exactly 35 frozen Binance symbols, and verifies the frozen official market WebSocket URL namespace.

## Scientific invariance

UNCHANGED:

- family and 35-asset frozen universe;
- Binance / Bitget / MEXC source identities;
- 1-minute closed-candle semantics;
- 5-minute lookback;
- external consensus = mean(Binance, Bitget);
- leader dispersion <=10 bps;
- abs MEXC 5m move >=40 bps;
- abs excess >=35 bps;
- same-sign rule;
- FADE_MEXC_EXCESS;
- +5m exit;
- 10m global cooldown;
- 13:35–19:55 UTC scan;
- notionals 10 / 25 / 50 / 100 USDT;
- primary 16 bps round-trip fee scenario;
- >=30 admitted event baskets and >=5 session dates;
- all PASS / FAIL / BLOCKED criteria.

No thresholds, assets, timings, costs, directions, sources or outcome gates are changed.

## Current classification

Historical family: `ROBUST_API_FEE_SURVIVOR`.

Forward execution remains `EXECUTION_SHADOW_UNDERPOWERED` until the frozen minimum prospective sample exists.

No orders, private endpoints, account reads, wallets, exchange mutation or live trading.
