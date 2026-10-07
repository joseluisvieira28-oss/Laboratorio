# MEXC GLOBAL-ASSET OVERSHOOT — V0.2.3 SOURCE INCIDENT RECEIPT

Date: 2026-10-07
Scope: completed V0.2.3 captures from 2026-10-05 and 2026-10-06 only.

Runs inspected: 37312427508, 37341450607, 37470945455, 37496306640.

Aggregate source errors: 9,962.
- MEXC_SUCCESS_FALSE: 9,099
- Bitget HTTP 429: 793
- Binance WS exact-points missing: 70

The MEXC failure pattern was highly regular: many scan minutes produced exactly 12 MEXC failures out of the 35 frozen candidates. Bitget failures were explicit HTTP 429 responses. This is consistent with transport/rate-limit pressure from the V0.2.3 per-minute REST fan-out and is the operational reason for V0.2.4 transport remediation.

No historical receipt is repaired or backfilled. V0.2.4 starts a clean prospective epoch after its freeze commit and replaces MEXC/Bitget signal K-line REST fan-out with public WebSocket caches while preserving the frozen science.

No orders, private endpoints, account reads, trading, main merge or post-outcome tuning.
