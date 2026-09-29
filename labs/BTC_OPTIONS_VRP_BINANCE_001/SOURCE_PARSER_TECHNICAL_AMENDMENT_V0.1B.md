# BTC-OPTIONS-VRP-BINANCE-001 — EXPIRY REGEX TECHNICAL AMENDMENT V0.1B

Date: 2026-09-19  
Parent gate: `BOVRP-BINANCE-EOH-SOURCE-001`  
Prior corrected run: `35461030556`

## Evidence

V0.1A proved all three frozen sample files contain complete bid/ask price and quantity fields, reconstructable point-in-time `date + hour`, option identity, right and strike. It still reported zero expiry parses.

Code inspection found a transport/escaping defect in the Python regular expression: the raw regex was committed as `\\d{6}`, matching a literal backslash plus d rather than the six-digit Binance expiry token.

Binance's published option-symbol convention uses a six-digit expiry token, for example `BTC-220815-50000-C`.

## Authorized correction

Change only the expiry-token regex from the incorrectly escaped literal pattern to `\d{6}`.

No source date, sample date, coverage threshold, semantic requirement, economic rule or outcome permission changes. No prices, returns, VRP or PnL are opened by this correction.
