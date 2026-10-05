# MEXC INTRADAY LARGE-SHOCK CATCH-UP — PRE-OUTCOME FREEZE V1.1

Date: 2026-10-05
Status: FROZEN BEFORE OUTCOMES

This is a new economic sub-family of the already replicated MEXC global-asset lead-lag mechanism. It asks whether only large observable leader shocks leave enough target catch-up magnitude to clear the documented standard API fee burden.

Universe: all 35 assets bound independently in V0.5. No asset selection after outcomes.
Sample: weekdays 2026-09-09 through 2026-10-02, excluding burned source date 2026-09-30.
Session: 14:31–18:39 UTC.

Single frozen trigger:
- external exact 1m return = mean(Binance + Bitget)
- abs external shock >=25 bps
- lag gap = external return - MEXC return
- same sign gap and external
- abs lag gap >=15 bps
- direction FOLLOW_EXTERNAL_CONSENSUS
- horizon 5m
- cooldown 5m

Scientific unit: equal-weight daily basket across all triggered assets/trades.
PASS requires >=30 trades, >=10 triggered days, positive mean and median daily gross, >50% winning days, both chronological halves positive, exact one-sided binomial p<0.05.

Economic PASS additionally requires BOTH mean and median daily gross >16 bps (equivalently positive after a 16 bps round-trip cost assumption).

No grid, no asset picking, no threshold rescue, no horizon rescue, no post-outcome tuning.
No private endpoints, account reads, orders, wallets, exchange mutation or live trading.
