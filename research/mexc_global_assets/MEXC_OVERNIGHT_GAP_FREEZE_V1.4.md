# MEXC OVERNIGHT GAP CATCH-UP BASKET — PRE-OUTCOME FREEZE V1.4

Date: 2026-10-05
Status: FROZEN BEFORE OUTCOMES

Source authority:
- run 37265690414
- artifact SHA256 `417b74417ac4462afb832f194753970e942ab97f1f8cf0aed8d3ab8adef5589d`
- 35/35 source-pass for previous cash-close + current cash-open transport
- current source date 2026-09-30 is excluded from outcomes

Frozen sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude current date 2026-09-30

Frozen signal:
- previous-session anchor: 20:00 UTC
- current signal/entry: 13:29 UTC
- external overnight return = mean(Binance + Bitget) previous 20:00 -> current 13:29
- MEXC overnight return = MEXC previous 20:00 -> current 13:29
- lag gap = external overnight return - MEXC overnight return
- trigger only if abs(external overnight return) >=100 bps
- require sign(lag gap) == sign(external overnight return)
- require abs(lag gap) >=25 bps
- FOLLOW_EXTERNAL_CONSENSUS
- exit MEXC at 13:59 UTC
- horizon 30 minutes

Basket:
- all triggered assets on the same current date are equal-weighted
- daily basket is the scientific unit

Scientific PASS:
- >=20 triggered trades
- >=8 triggered dates
- mean daily gross >0
- median daily gross >0
- winning-day rate >50%
- both chronological halves mean >0
- exact one-sided binomial p<0.05 over triggered days

Operational robust survivor:
- scientific PASS
- mean daily net after 16 bps >0
- median daily net after 16 bps >0

No asset-specific tuning, threshold grid, horizon grid, retrospective rescue, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
