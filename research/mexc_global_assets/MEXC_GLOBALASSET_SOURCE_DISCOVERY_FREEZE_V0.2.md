# MEXC GLOBAL-ASSET OPERATIONAL SOURCE DISCOVERY V0.2

Date: 2026-10-04
Status: SOURCE-ONLY / PRE-OUTCOME

Purpose:
Find all current MEXC contracts that share the same declared index architecture already observed in NVIDIA_USDT and TESLA_USDT:

- BINANCE_FUTURE
- BITGET_FUTURE
- BINANCETICKER
- PYTH
- KAIKO

The scan is source-only. It may use symbol identity and transport availability, but must not compute returns, lag, direction, signals, wins/losses or PnL.

Verification date:
2026-09-30

Verification date is burned from any later outcomes.

For each matching MEXC contract, the default public/free external alias is root+USDT on Binance Futures and Bitget Futures. A triple-source PASS requires >=260 MEXC/Binance core minutes and >=240 Bitget rows in the source-verification window.

NVIDIA_USDT and TESLA_USDT may appear as calibration/source candidates but are forbidden from any new outcome family because their outcomes are already open.

No private endpoints, account reads, orders, wallets, exchange mutation or live trading.
