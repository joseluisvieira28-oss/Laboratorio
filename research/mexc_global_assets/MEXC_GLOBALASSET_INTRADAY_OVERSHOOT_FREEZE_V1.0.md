# MEXC GLOBAL-ASSET — INTRADAY OVERSHOOT SNAPBACK
## PRE-OUTCOME FREEZE V1.0

Date: 2026-10-05
Status: FROZEN BEFORE OUTCOMES

Economic mechanism:
This is not another follower catch-up threshold variant. It tests the opposite state: MEXC itself moves materially farther than a tightly agreeing Binance+Bitget external consensus, and the trade fades the MEXC-specific excess.

Source gate:
- exact full-session public/free source requirements already passed in run 37282772060
- 35/35 MEXC + Binance + Bitget identities
- 1m coverage 13:30–20:00 UTC
- burned source date 2026-09-30 remains excluded

Frozen sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude 2026-09-30
- scan closed timestamps 13:35 through 19:55 UTC

Frozen signal:
- lookback = 5 minutes
- external consensus = mean(Binance 5m return, Bitget 5m return)
- leader quality requires abs(Binance return - Bitget return) <=10 bps
- MEXC 5m absolute move >=40 bps
- MEXC excess = MEXC 5m return - external consensus 5m return
- abs(MEXC excess) >=35 bps
- sign(MEXC excess) == sign(MEXC 5m return)
- direction = FADE_MEXC_EXCESS
- enter at MEXC signal close
- exit exactly +5m

Dependence control:
- simultaneous assets -> one equal-weight event basket
- global cooldown = 10 minutes after an admitted event timestamp
- all admitted event baskets on the same date -> one equal-weight daily basket
- daily basket is the scientific unit

Scientific PASS:
- >=20 admitted event baskets
- >=8 triggered dates
- mean daily gross >0
- median daily gross >0
- win-day rate >50%
- both chronological half means >0
- exact one-sided binomial p<0.05

Operational:
- 0 / 12 / 14 / 16 / 20 bps round-trip cost scenarios
- serious candidate only if scientific PASS and mean+median remain >0 after 16 bps

No per-asset tuning, no threshold grid, no horizon grid, no retrospective rescue, no post-outcome tuning.
No private endpoints, account reads, orders, wallets, exchange mutation or live trading.
