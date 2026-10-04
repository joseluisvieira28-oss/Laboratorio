# MEXC NVIDIA CASH-CLOSE SOURCE GATE V0.3

Date: 2026-10-04
Status: SOURCE-ONLY / PRE-OUTCOME

Purpose:
- verify public/free historical transport around the U.S. cash close for MEXC NVIDIA_USDT, Binance NVDAUSDT and Bitget NVDAUSDT;
- use 2026-09-30 only as a source-verification date;
- confirm that the 19:50-20:35 UTC window is technically recoverable before any cash-close outcome is scored.

No basis, momentum, return, direction, win/loss or PnL is computed in this source gate.

The intended economic mechanism is separate from the cash-open study:
after 20:00 UTC, cash-equity-linked sources such as Pyth/Kaiko cease regular-session updates while 24/7 crypto futures continue. Any later hypothesis must be frozen before outcomes.

No private endpoints, account reads, wallets, orders, exchange mutation or live trading are authorized.
