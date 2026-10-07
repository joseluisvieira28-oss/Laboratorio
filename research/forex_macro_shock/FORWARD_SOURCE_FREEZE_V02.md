# FOREX-MACRO-SHOCK-001 — EUR/ECB FORWARD SOURCE FREEZE V0.2

Date: 2026-10-07
Status: FROZEN BEFORE ANY V0.2 ECONOMIC OUTCOME

## Parent authority

Historical V0.1 remains `SOURCE_BLOCKED` for Development/OOS because sufficient historical MEXC coverage was not proven.
This V0.2 does not revise that verdict and does not backfill historical event windows.

## Protected future event

Primary protected event:
- ECB monetary-policy meeting: 2026-10-29
- scheduled policy decision publication: 14:15 Europe/Berlin on that date = 13:15 UTC
- press conference: 14:45 Europe/Berlin = 13:45 UTC

The policy-decision release and the later press conference are separate mechanisms.
No V0.2 market outcome around 2026-10-29 may be opened before a later complete economic-signal freeze.

## Candidate source identity

Target:
- MEXC `EUR_USDT` perpetual

Independent external observable:
- Binance Spot `EURUSDT`

Official event authority:
- ECB monetary-policy decision publication

Optional secondary source-validation only:
- Dukascopy EURUSD
- MEXC index/fair price as diagnostics only, NOT independent venues

MEXC index price may contain external venues and must not be counted as independent confirmation of Binance.

## V0.2 scope: source/clock only

This V0.2 may collect and validate:
- MEXC public EUR_USDT market timestamps, kline/ticker/book data
- Binance public EURUSDT spot bookTicker and/or kline timestamps
- local UTC receive timestamps
- reconnect/gap logs
- ECB scheduled clock
- ECB first-seen publication URL/body hash/HTTP timestamp when the release becomes available

This V0.2 MUST NOT:
- calculate macro surprise
- use consensus
- calculate strategy PnL
- optimize thresholds
- select a profitable holding horizon
- infer direction from later returns
- score the 29 October event economically

## T0 policy

Scheduled time is not T0.

For a later policy-decision study:
T0 must be the first defensible timestamp at which the collector observes the official ECB decision publication, with URL and content hash preserved.

If exact first-seen publication cannot be measured defensibly, the event is source-invalid for any latency claim.

## Burn-in boundary

Pre-event live market capture may be used ONLY to establish:
- source availability
- timestamp alignment
- missingness
- reconnect behavior
- normal feed latency
- executable book availability

Burn-in may not be used to choose a profitable threshold or horizon.

A separate immutable economic-signal freeze must be committed before opening 2026-10-29 outcomes.

## Source-ready gate

`FORWARD_SOURCE_ARMED` requires:
1. MEXC EUR_USDT public feed works without auth;
2. Binance EURUSDT public spot feed works without auth;
3. timestamps can be aligned in UTC;
4. exact closed-minute or real-time book observations are distinguishable;
5. stale/missing data fail closed;
6. ECB watcher can record scheduled metadata and a first-seen content hash path;
7. no private/account/trading endpoint is needed.

Otherwise use `FORWARD_SOURCE_BLOCKED` with the exact blocker.

## Governance

No main merge.
No orders.
No private endpoints.
No account reads.
No wallets.
No exchange mutation.
No spending.
No live trading.
No consensus fabrication.
No historical rescue.
No post-outcome tuning.
