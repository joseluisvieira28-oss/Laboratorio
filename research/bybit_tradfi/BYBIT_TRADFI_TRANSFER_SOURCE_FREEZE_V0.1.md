# BYBIT TRADFI TRANSFER — SOURCE GATE V0.1

Date: 2026-10-05
Status: SOURCE-ONLY / PRE-OUTCOME

Purpose:
Determine which members of the previously frozen 35-asset global-asset universe have complete public/free 1-minute transport on:
- Bybit TradFi perpetual target
- Binance Futures external leg
- Bitget Futures external leg

No return, lag, direction, win/loss or PnL may be computed in this gate.

Candidate universe is frozen before Bybit outcomes and contains all 35 assets from the prior MEXC V0.5 family, mapped to their direct ticker aliases.

Burned source-verification date:
2026-08-14

Verification window:
14:30–19:00 UTC

PASS per candidate requires:
- Bybit linear instrument exists and is Trading;
- Bybit 1m target history has >=260 core minutes;
- Binance official Futures Vision 1m archive has >=260 core minutes;
- Bitget public 1m futures history has >=240 rows.

Source availability may filter candidates.
No outcome statistic may filter candidates.

If one or more candidates pass, a separate pre-outcome freeze MUST be committed before opening any Bybit target outcomes.

No private endpoints, account reads, orders, wallets, exchange mutation or live trading.
