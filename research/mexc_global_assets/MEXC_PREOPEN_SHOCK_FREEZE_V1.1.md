# MEXC PRE-OPEN SHOCK CATCH-UP BASKET — PRE-OUTCOME FREEZE V1.1

Date: 2026-10-05
Status: FROZEN BEFORE OUTCOMES

Source authority:
- run 37264942309
- artifact ID 11325902512
- artifact SHA256 `93d39e769e874d1c778c4978eda4a570494ff30b54e33a087a2c08198cb12e06`
- 35/35 public MEXC + Binance + Bitget sources pass on the burned source date 2026-09-30.

Frozen sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude 2026-09-30

Frozen signal:
- measure each asset from exact closed-candle timestamp 12:29 to 13:29 UTC
- external 60m return = mean(Binance return, Bitget return)
- MEXC 60m return measured over the same timestamps
- lag gap = external return - MEXC return
- trigger only if abs(external return) >= 75 bps
- require sign(lag gap) == sign(external return)
- require abs(lag gap) >= 25 bps
- direction = FOLLOW_EXTERNAL_CONSENSUS
- enter MEXC at 13:29 close
- exit at 13:34 close
- horizon = 5 minutes

Basket:
All triggered assets on the same date are equal-weighted into one daily basket observation.
The daily basket is the scientific unit, specifically to reduce false confidence from cross-sectional dependence.

Scientific PASS:
- >=20 total triggered trades
- >=8 triggered dates
- mean daily basket gross >0
- median daily basket gross >0
- winning-day rate >50%
- both chronological halves of daily basket means >0
- exact one-sided binomial p<0.05 across triggered days

Operational:
- fees evaluated at 0 / 12 / 14 / 16 / 20 bps round trip per trade
- robust API-fee survivor requires scientific PASS AND mean daily net after 16 bps >0 AND median daily net after 16 bps >0

No asset-specific tuning, threshold grid, horizon grid, retrospective rescue, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
