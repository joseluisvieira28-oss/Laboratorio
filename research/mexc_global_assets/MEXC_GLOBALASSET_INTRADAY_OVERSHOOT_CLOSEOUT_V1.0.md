# MEXC GLOBAL-ASSET — INTRADAY OVERSHOOT SNAPBACK V1.0 — CLOSEOUT

Date: 2026-10-05
Outcome run: 37283930479
Outcome artifact ID: 11333552614
Outcome artifact ZIP SHA256: `d1350734517595ac0b496f5c6a054d20e008255baa17fcb5db57713b97a1d1f4`

Frozen mechanism:
- target-specific MEXC overshoot relative to tightly agreeing Binance + Bitget external consensus
- 5m lookback
- leader dispersion <=10 bps
- abs MEXC 5m move >=40 bps
- abs MEXC excess vs external consensus >=35 bps
- FADE_MEXC_EXCESS
- +5m exit
- global cooldown 10m
- simultaneous assets -> event basket
- daily basket = scientific unit

Results:
- raw trigger rows: 221
- admitted event baskets: 143
- triggered days: 17
- winning days: 17/17
- win-day rate: 100%
- exact one-sided binomial p = 0.00000762939453125
- chronological half means: +24.6167 / +16.0511 bps
- mean daily gross: +20.0820 bps
- median daily gross: +18.2504 bps

Cost scenarios:
- 12 bps RT: mean +8.0820 / median +6.2504 bps
- 14 bps RT: mean +6.0820 / median +4.2504 bps
- 16 bps RT: mean +4.0820 / median +2.2504 bps
- 20 bps RT: mean +0.0820 / median -1.7496 bps

Verdict:
`ROBUST_API_FEE_SURVIVOR`

This is a serious scientific/economic survivor under the frozen fee scenarios, but NOT live-go and NOT yet a cana. Public execution feasibility must now validate spread, depth/slippage, latency and fill assumptions during the same 13:30–20:00 UTC session.

No post-outcome tuning, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
