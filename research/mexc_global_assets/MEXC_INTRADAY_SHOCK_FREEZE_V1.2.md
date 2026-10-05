# MEXC INTRADAY LARGE-SHOCK CATCH-UP BASKET — PRE-OUTCOME FREEZE V1.2

Date: 2026-10-05
Status: FROZEN BEFORE OUTCOMES

Source authority:
- 35/35 global-asset aliases with regular-session MEXC + Binance + Bitget transport previously proven.
- source authority run 37235636339
- artifact SHA256 94f8a3865c6f6619a9cebf1ca8c546557cb538579c01fc1f82e26d7416b0b78a
- 2026-09-30 remains burned.

Frozen sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude 2026-09-30
- signals 14:35–18:39 UTC

Frozen mechanism:
- 5-minute external return = mean(Binance, Bitget)
- 5-minute MEXC return over same timestamps
- trigger only when abs(external) >= 30 bps
- require lag gap in same direction as external
- require abs(external - MEXC) >= 20 bps
- FOLLOW_EXTERNAL_CONSENSUS
- enter at signal close; exit 5 minutes later
- 5-minute cooldown per asset

Scientific unit:
- equal-weight daily basket of every triggered asset/trade that day.

PASS:
- >=50 total trades
- >=10 triggered days
- mean and median daily gross >0
- winning-day rate >50%
- both chronological half means >0
- exact one-sided binomial p<0.05

Operational survivor:
- scientific PASS
- mean daily net after 16 bps >0
- median daily net after 16 bps >0

No threshold/horizon grid, asset-specific tuning, rescue, account reads, private endpoints, orders, wallets, exchange mutation or live trading.
