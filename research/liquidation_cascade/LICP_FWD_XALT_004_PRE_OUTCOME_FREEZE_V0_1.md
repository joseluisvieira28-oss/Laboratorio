# LICP-FWD-XALT-004 — BTC LIQUIDATION IGNITION -> MEXC SOL 60M
## PRE-OUTCOME TRANSFER FREEZE V0.1

Date: 2026-09-26
Status: PRE-OUTCOME / BLOCKED UNTIL LICP-001 NUMERIC TRIGGER CONFIG IS FROZEN

## Provenance
Historical predecessor:
LICP-HIST-XALT-003

Historical frozen candidate that survived single-pass holdout:
- BTC liquidation ignition
- SOL short continuation
- 60-minute horizon

This forward study tests transferability. It does NOT alter the historical result.

## Source-transfer boundary
Historical event timing came from a complete Hyperliquid liquidation archive.
No equivalent complete global real-time Hyperliquid liquidation firehose has been established for this lab.

Therefore the forward trigger is explicitly a NEW source-transfer implementation:
- primary ignition: Bybit BTCUSDT allLiquidation
- confirmation: Binance BTCUSDT forceOrder
- target: MEXC SOL_USDT executable BBO

A forward failure does not retroactively invalidate the historical result; it rejects transfer through this live sensor/execution path.

## Trigger
The study MUST use the frozen numeric LICP-001 trigger configuration.

It may not start while:
LICP_001_TRIGGER_CONFIG_V0_1.json.status != FROZEN

Eligible event:
- BTC_CONFIRMED only
- forced pressure MUST be SELL
- 120-second episode cooldown
- no ETH/SOL second-wave requirement
- no BUY/reversal family

## Entry
At confirmed BTC ignition:
- wait exactly 60 seconds
- take the first fresh, non-crossed MEXC SOL_USDT BBO at or after the delay
- virtual SHORT taker entry = best bid

This 60-second delay is frozen before forward outcomes and is the live analogue of the historical one-minute processing delay after the coarse trigger became observable.

## Exit
- horizon = exactly 60 minutes after entry
- take first fresh, non-crossed SOL_USDT BBO at or after the horizon
- virtual SHORT taker exit = best ask

gross_bps = (entry_bid - exit_ask) / entry_bid * 10,000
net_taker_bps = gross_bps - 16

No maker rescue.
No alternative horizon.
No stop-loss optimization.
No take-profit optimization.

## Evidence rule
No verdict before:
- >= 20 independent BTC_CONFIRMED SELL episodes
- >= 3 distinct UTC dates
- missing/stale entry-or-exit rate <= 10%

FORWARD_TRANSFER_SURVIVES only if:
- mean net_taker_bps > 0
- median gross_bps > 0
- >= 2 distinct UTC dates have positive mean gross_bps

Otherwise:
- insufficient evidence => FORWARD_INSUFFICIENT
- sufficient evidence but criteria fail => FORWARD_TRANSFER_FAIL

## Governance
Research/shadow only.
No orders.
No authentication.
No exchange mutation.
No capital.
No live-trading authority.
No main merge.
