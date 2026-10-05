# MEXC GLOBAL-ASSET — INTRADAY OVERSHOOT SNAPBACK
## SOURCE GATE V1.0

Date: 2026-10-05
Status: SOURCE PASS BY EXACT SOURCE-REQUIREMENT INHERITANCE

Required data:
- the same 35 MEXC global-asset contracts
- the same Binance and Bitget public/free external leaders
- 1-minute closed-candle data across 13:30–20:00 UTC
- same 2026-09-09 through 2026-10-02 research window
- burned source date 2026-09-30 excluded from outcomes

Authority reused without opening outcomes:
- full-session public/free source gate run: 37282772060
- artifact ID: 11332209029
- report SHA256: `9f38273c7ed4673bd4da05c2a4268412b76e052fd7570d9da4bd00ec7a7fb61c`
- artifact ZIP SHA256: `961f3214ce7de25d1dc0e473f5f5f8412bd647b1529d1bd09af224676f2d271f`
- 35/35 assets returned 391 usable 1-minute closed timestamps on MEXC, Binance and Bitget over the frozen full-session source window.

Why reuse is valid:
This family requires no new venue, symbol, cadence or session coverage beyond the already-proven full-session source gate. Re-running the identical source probe would not add scientific information.

Verdict:
`SOURCE_PASS`

No returns, PnL, private endpoints, account reads, orders, wallets, exchange mutation or live trading were opened by this source gate.
