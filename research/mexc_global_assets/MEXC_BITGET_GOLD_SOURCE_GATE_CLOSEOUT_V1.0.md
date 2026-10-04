# MEXC ↔ BITGET GOLD/XAU — SOURCE GATE CLOSEOUT V1.0

Date: 2026-10-04
Run: 37195951549
Artifact SHA256: `e4be7400c5a9312217730f8caf6cf853f28c17523e9580b703546992c8765f95`

Verdict:
`MEXC_BITGET_GOLD_SOURCE_PASS`

Evidence:
- MEXC exact `XAU_USDT`, apiAllowed=true;
- MEXC indexOrigin includes `BITGET_FUTURE`;
- Bitget exact `XAUUSDT`, XAU identity confirmed;
- public/no-auth live market data on both venues;
- public/no-auth 1m candles on both venues;
- MEXC index vs Bitget mid snapshot difference approximately -1.4356 bps;
- outcomes opened: 0;
- no accounts, wallets, credentials, orders, mutation or live trading.

Prior Global Asset GOLD research used June-August and did not fetch September.
Any V1.1 outcome research must use a new freeze and exclude those prior periods.
