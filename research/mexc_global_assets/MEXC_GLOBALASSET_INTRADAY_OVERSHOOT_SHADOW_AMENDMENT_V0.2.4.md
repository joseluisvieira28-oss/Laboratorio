# MEXC GLOBAL-ASSET INTRADAY OVERSHOOT — SHADOW TRANSPORT AMENDMENT V0.2.4

Date: 2026-10-07
Branch: `mexc-globalasset-intraday-overshoot-shadow-v0.2.4-ws-remediation-2026-10-07`
Parent scientific authority: `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_FREEZE_V0.2.md`
Parent technical authorities:
- `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_AMENDMENT_V0.2.1.md`
- `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_AMENDMENT_V0.2.2.md`
- `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_AMENDMENT_V0.2.3.md`

Status: FROZEN TECHNICAL TRANSPORT REMEDIATION BEFORE ANY V0.2.4 ECONOMIC OUTCOME

## Why this amendment exists

Prospective V0.2.3 capture runs completed at workflow level but accumulated large numbers of source errors. The collector queried up to 35 MEXC K-line REST routes concurrently and up to 35 Bitget K-line REST routes concurrently every scan minute.

Official public documentation states:
- MEXC contract K-line REST rate limit: 20 requests / 2 seconds.
- MEXC public WebSocket: `wss://contract.mexc.com/edge`; K-line subscription method `sub.kline`; public connections require ping within one minute and recommend ping every 10–20 seconds.
- Bitget public market REST candlestick rate limit: 20 requests / second / IP.
- Bitget provides public WebSocket candlestick channels.

This amendment changes TRANSPORT ONLY to remove avoidable REST fan-out pressure.

## Prospective boundary

No V0.2.4 observation may have a signal timestamp at or before the commit timestamp that first adds this amendment.

V0.2.4 execution evidence is a CLEAN prospective epoch.

V0.2.3 receipts from 2026-10-05 through 2026-10-07 remain preserved as historical operational evidence but MUST NOT be pooled into the V0.2.4 execution-feasibility sample unless a later pre-outcome authority explicitly permits such pooling. Default behavior is NO POOLING.

No missed or invalid V0.2.3 observation may be backfilled.

## Scientific invariance — unchanged

The following remain EXACTLY unchanged:
- family: `MEXC-GLOBALASSET-INTRADAY-OVERSHOOT-SNAPBACK-V1.0`
- frozen 35-asset universe and all MEXC/Binance/Bitget identities
- 1-minute CLOSED-candle semantics
- 5-minute lookback
- external consensus = mean(Binance 5m return, Bitget 5m return)
- leader quality: abs(Binance return - Bitget return) <= 10 bps
- abs MEXC 5m move >= 40 bps
- abs MEXC excess >= 35 bps
- same-sign excess/MEXC rule
- direction = FADE_MEXC_EXCESS
- entry at first timing-qualified executable MEXC public book after the frozen signal close
- exit at timing-qualified executable MEXC public book exactly +5m
- entry/exit timing qualification 0–30 seconds
- same-contract entry/exit quantity invariant
- global cooldown = 10 minutes
- simultaneous assets form one equal-weight event basket
- daily basket remains the reporting unit
- notionals = 10 / 25 / 50 / 100 USDT
- primary fee scenario = 16 bps round trip
- sensitivity fees = 12 / 14 / 20 bps
- minimum evidence = >=30 admitted shadow event baskets AND >=5 distinct session dates
- all PASS / FAIL / BLOCKED criteria
- no maker-fill assumption
- no asset-specific tuning
- no threshold grid
- no horizon grid
- no retrospective rescue
- no post-outcome tuning

## Frozen V0.2.4 transport

### Binance
Preserve V0.2.2 transport unchanged:
- official Binance USD-M public market WebSocket
- exact frozen Binance symbols
- closed 1m candles only
- exact t-5m and t points required
- raw messages, hashes, event/receive timestamps retained

### MEXC
Replace signal K-line REST polling with public WebSocket K-line cache:
- URL: `wss://contract.mexc.com/edge`
- subscription: `{"method":"sub.kline","param":{"symbol":"<FROZEN_MEXC_SYMBOL>","interval":"Min1"}}`
- exact frozen 35 MEXC symbols only
- `push.kline` only
- candle field `t` is window start in seconds; observable close timestamp = `t + 60`
- close field = `c`
- preserve raw message, SHA-256, receive timestamp, MEXC `ts` when present
- send `{"method":"ping"}` every 15 seconds
- reconnect fail-closed; gaps are logged and are never reconstructed retrospectively
- exact t-5m and t closed points required

MEXC public REST remains allowed ONLY for:
- one contract metadata request at startup, subject to its documented rate limit;
- entry/exit depth snapshots after actual frozen triggers, using existing V0.2.1 execution model.

No MEXC signal K-line REST fan-out is permitted in V0.2.4.

### Bitget
Replace signal K-line REST polling with public WebSocket candlestick cache.
Preferred current public transport:
- `wss://ws.bitget.com/v3/ws/public`
- exact frozen Bitget USDT-futures symbols only
- K-line topic, interval 1m
- fewer than 50 channels per connection; 35 frozen channels fit the documented recommendation
- ping/pong handling per public WebSocket documentation
- preserve raw messages, hashes, exchange/receive timestamps where exposed
- exact t-5m and t closed points required

If the v3 public K-line payload cannot be parsed or subscribed reliably in outcome-blind transport tests, an equivalent documented Bitget public v2 `candle1m` transport may be used, but the source identity and closed-candle semantics must remain unchanged and the chosen transport must be documented before any V0.2.4 economic observation.

No Bitget signal K-line REST fan-out is permitted in V0.2.4.

## Outcome-blind remediation tests

Before any V0.2.4 economic capture, tests must validate:
1. all 35 frozen MEXC identities are subscribed;
2. all 35 frozen Bitget identities are subscribed;
3. all 35 frozen Binance identities remain subscribed;
4. caches ingest public messages without authentication;
5. exact closed-minute mapping is deterministic;
6. raw message hashes and receive timestamps are stored;
7. reconnect/gap errors are explicit;
8. no REST K-line fan-out remains for MEXC or Bitget;
9. same-contract execution invariant still passes;
10. empty prospective sample remains `EXECUTION_SHADOW_UNDERPOWERED`.

Transport/burn-in probes MUST NOT be scored as economic outcomes.

## Fail-closed rules

If any required exact closed point is missing, stale, ambiguous or from a disconnected source:
- do not generate a valid signal for that asset/minute;
- log source failure;
- do not backfill later.

If public transport cannot provide defensible frozen source data:
`EXECUTION_SOURCE_BLOCKED`.

If transport passes but sample is below the frozen gate:
`EXECUTION_SHADOW_UNDERPOWERED`.

## Governance

No orders.
No private/authenticated endpoints.
No account reads.
No balances or positions.
No wallets.
No exchange mutation.
No live trading.
No spending.
No merge to main.
No changes to scientific thresholds, costs, directions, windows or outcome gates.
