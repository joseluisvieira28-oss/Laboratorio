# MEXC EARNINGS-SHOCK SOURCE GATE V2.0.3 — CONSERVATIVE TIMING

Date: 2026-10-05
Status: SOURCE-ONLY / PRE-OUTCOME

Nasdaq's historical Earnings Calendar exposes date+symbol reliably, but historical rows report `time-not-supplied`.

To eliminate timing ambiguity without using price outcomes:
- every matched earnings-calendar date is mapped to the NEXT WEEKDAY trading session;
- no same-day session is ever used;
- EPS, surprise and forecast fields are ignored entirely.

Thus the earnings event is known before the eligible session regardless of whether the original report occurred pre-market, during market hours or after-hours.

Period: July–August 2026.
Market source requirement: public MEXC + Binance Futures + Bitget Futures 1m transport over 12:20–13:40 UTC.

No returns, gaps, signals, direction, wins/losses or PnL in this gate.
No private endpoints, account reads, wallets, orders, exchange mutation or live trading.
