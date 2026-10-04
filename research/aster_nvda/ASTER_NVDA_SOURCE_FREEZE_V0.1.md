# ASTER NVDA PORTABILITY SOURCE GATE V0.1

Date: 2026-10-05
Status: SOURCE-ONLY / PRE-OUTCOME

Aster official V3 documentation exposes public market data at https://fapi.asterdex.com including exchangeInfo, klines and depth without account authentication.

This gate discovers any NVDA futures symbol from exchangeInfo and tests 1m historical transport on the burned source date 2026-09-30 plus a current L2 snapshot.

No returns, signals, PnL, account reads, wallets, orders or live trading.
