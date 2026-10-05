# MEXC GLOBAL-ASSET INTRADAY OVERSHOOT — SHADOW SOURCE TRANSPORT AMENDMENT V0.2.2

Date: 2026-10-05
Branch: `mexc-globalasset-intraday-overshoot-shadow-v0.2.1-remediation-2026-10-05`
Parent: `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_AMENDMENT_V0.2.1.md`
Status: FROZEN BEFORE ANY VALID FORWARD OUTCOME

## Trigger

GitHub-hosted runners receive HTTP 451 from the Binance USD-M REST endpoint
`https://fapi.binance.com/fapi/v1/klines`.

The alternative `fapi1`–`fapi4` hosts did not return usable 200 market-data payloads
from the runner.

A public/no-auth probe against the current official Binance USD-M market WebSocket passed:

`wss://fstream.binance.com/market/ws/mstrusdt@kline_1m`

Binance documentation published in 2026 maps kline/candlestick streams to the new
`/market` WebSocket namespace and states that the legacy URL was retired on
2026-04-23.

## Scientific invariance

This amendment changes TRANSPORT ONLY.

Unchanged:
- Binance instrument identities frozen in V1.0 source binding;
- Bitget identities;
- MEXC targets;
- 1-minute closed-candle semantics;
- 5-minute return construction;
- external consensus = mean(Binance, Bitget);
- leader dispersion <=10 bps;
- abs MEXC 5m move >=40 bps;
- abs excess >=35 bps;
- same-sign rule;
- FADE_MEXC_EXCESS;
- +5m exit;
- 10m global cooldown;
- 13:35–19:55 UTC closed-candle scan;
- all statistical and execution gates.

No historical or forward outcome was opened to choose this transport.

## Frozen Binance transport

Use:
`wss://fstream.binance.com/market/stream?streams=<symbol>@kline_1m/...`

For each frozen Binance symbol:
- accept only event type `kline`;
- accept only closed klines (`k.x == true`);
- map candle open time `k.t` to observable close timestamp `k.t/1000 + 60`;
- preserve the exact raw WebSocket message, SHA-256, receive timestamp and Binance event timestamp;
- require the exact two points `t-5m` and `t`;
- missing exact points fail closed.

The combined connection may carry all 35 frozen Binance symbols; no symbol substitution is allowed.

## Important out-of-session note

Public MEXC order books for several equity perpetuals are unavailable/inactive before
the frozen US cash-session window. Those out-of-session failures are NON-EVIDENTIARY
because V0.2 already required execution evidence only inside 13:30–20:00 UTC.

In-session book/source failures remain fail-closed.

## Current classification

Historical family:
`ROBUST_API_FEE_SURVIVOR`.

Forward execution:
`EXECUTION_SHADOW_UNDERPOWERED`.

Reason:
the frozen execution gate requires >=30 admitted shadow event baskets across >=5 distinct
session dates. Those future observations do not yet exist.

No live trading, orders, private endpoints, account reads, wallets or exchange mutation.
