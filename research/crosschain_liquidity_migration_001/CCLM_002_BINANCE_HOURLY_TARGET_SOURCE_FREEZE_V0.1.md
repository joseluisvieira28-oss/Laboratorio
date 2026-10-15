# CCLM-002 BINANCE HOURLY TARGET SOURCE GATE V0.1

Frozen: 2026-09-25
Stage: TARGET SOURCE INTEGRITY ONLY
Flow/price relationship: CLOSED

Parent discovery freeze requires official Binance historical spot archives for:
- AVAXUSDT
- BTCUSDT

Primary target later uses hourly closes. This source gate does NOT compute any
return or join price data to CCTP flow.

## Frozen fixture

Calendar month: 2023-05
Venue/archive: Binance Data Vision official spot monthly klines
Interval: 1h
Symbols: AVAXUSDT, BTCUSDT

Expected path:
data/spot/monthly/klines/<SYMBOL>/1h/<SYMBOL>-1h-2023-05.zip

## PASS requirements per symbol

- .CHECKSUM file resolves;
- downloaded ZIP SHA256 exactly matches checksum;
- exactly one expected CSV member;
- open timestamps are strictly increasing;
- every adjacent open timestamp differs by exactly 3,600,000 ms;
- first open = 2023-05-01T00:00:00Z;
- last open = 2023-05-31T23:00:00Z;
- 744 hourly rows;
- no price/return value is persisted in the receipt.

Passing authorizes the frozen Discovery implementation to use the same archive
family for the predeclared 2023-05 through 2024-12 periods, subject to identical
integrity checks for every monthly file actually opened.

No market outcome is opened by this gate.
