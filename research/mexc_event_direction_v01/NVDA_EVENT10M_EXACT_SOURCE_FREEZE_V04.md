# NVIDIA EVENT-10M V0.4 — EXACT PUBLIC PRODUCT + INDEX STREAM SOURCE GATE

Frozen 2026-10-29 before data fetch. Read-only source gate, no forecasts, outcomes, price parity, accounts or orders.

- Source A: anonymous MEXC Event Futures UI page, GET-only route filtering (block non-GET and account/private/position/order/wallet). Capture publicly displayed official /api/platform/futures/api/v1/event_contract/detail as JSON raw byte hash; require NVIDIA_USDT state ONLINE and cycleConfigMap MINUTE 10 with positive exact upPayRate/downPayRate. Product is time-dependent; not historical.
- Source B: anonymous public wss://futures.mexc.com/edge subscription {"method":"sub.index.price","param":{"symbol":"NVIDIA_USDT"}}, read up to 30 seconds, require valid push.index.price NVIDIA_USDT with positive price and raw frame SHA256. Source B public INDEX is not proven identical to Event Futures actual executed order openPrice or contract server expiry index.
- Capture both receive timestamps in UTC milliseconds, response/body hashes, no cookies/login, no keys, no GET account data, no market outcome evaluation. A pass proves accessible public sources, not <=10 sec simultaneous decision-ready payout/<=2sec tick continuity and not economic edge.
- Existing protected NVIDIA V0.6 Oct5-30 forward remains sealed. Original prior cash-open no candidate remains closed. New paper November freeze is unchanged. No paid services/main merge/trading.
