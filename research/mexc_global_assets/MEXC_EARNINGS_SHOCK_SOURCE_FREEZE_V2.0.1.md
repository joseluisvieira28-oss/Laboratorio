# MEXC EARNINGS-SHOCK SOURCE GATE V2.0.1 — NASDAQ FALLBACK

Date: 2026-10-05
Status: SOURCE-ONLY / PRE-OUTCOME

The original SEC V2.0 source runner failed before opening outcomes because SEC returned HTTP 403 to the GitHub Actions runner.

This technical source revision does not change the scientific family. No outcomes have been opened.

Event authority:
- Nasdaq public Earnings Calendar endpoint.
- July/August 2026 only.
- only rows whose timing explicitly identifies PRE-MARKET or AFTER-HOURS are eligible.
- PRE-MARKET -> same weekday session.
- AFTER-HOURS -> next weekday session.
- ambiguous / time-not-supplied rows are excluded.

For each eligible event, MEXC target, Binance Futures external and Bitget Futures external must have public 1-minute transport over 12:20–13:40 UTC.

No returns, shocks, gaps, signals, wins/losses or PnL are computed in this gate.
No private endpoints, account reads, wallets, orders, exchange mutation or live trading.
