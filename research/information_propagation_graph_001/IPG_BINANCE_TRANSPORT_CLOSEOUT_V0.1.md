# IPG-001 BINANCE FORWARD TRANSPORT REMEDIATION CLOSEOUT V0.1

Date: 2026-09-24
Stage: FORWARD SOURCE TRANSPORT
Outcome access: CLOSED

## First public-source smoke

Deribit:
- BTC-PERPETUAL trades: PASS
- option-chain markprice packets: PASS
- BTC DVOL packets: PASS

Binance:
- Spot stream.binance.com:9443: HTTP 451
- USD-M fstream.binance.com: no events before timeout

## Prospectively frozen official transport matrix

Spot:
- stream.binance.com:9443 -> HTTP 451
- stream.binance.com:443 -> HTTP 451
- data-stream.binance.vision -> PASS, realtime BTCUSDT aggTrade
- data-api.binance.vision REST diagnostic -> PASS

USD-M Futures:
- fstream raw -> timeout / no event
- fstream combined -> timeout / no event
- fstream SUBSCRIBE -> timeout / no event
- fapi.binance.com REST diagnostic -> HTTP 451 restricted-location response

## Verdict

BINANCE_SPOT_FORWARD_TRANSPORT_PASS
BINANCE_USDM_FORWARD_TRANSPORT_BLOCKED_IN_GITHUB_HOSTED_RUNNER

The Spot collector route is remediated to Binance's official market-data-only
data-stream.binance.vision endpoint.

The USD-M Futures failure is treated as execution-environment/source-access
blocking, not as missing market activity and not as evidence about IPG edge.

REST cannot replace the Futures WebSocket for receive-time propagation
measurement. No proxy, Binance.US, testnet or alternative venue is allowed as
a silent substitute.

## Overall IPG forward-source status

- Deribit options/perp/DVOL live binding: PASS
- Binance Spot live binding: PASS
- Binance USD-M perp live binding in current GitHub runner: BLOCKED

Therefore:
FORWARD_PUBLIC_SOURCE_SMOKE_BLOCKED_BINANCE_USDM_GHA_LOCATION

The >=24h COLLECTOR_VALID gate is not opened until an authorized execution
environment can access the official USD-M market stream without timing-altering
proxying.

No market outcome, signal, PnL, order, exchange mutation or merge occurred.
