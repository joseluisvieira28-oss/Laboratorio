# ASTER NVDA PORTABILITY — PRE-OUTCOME FREEZE V0.2

Date: 2026-10-05
Status: FROZEN BEFORE OUTCOMES

Source gate run 37239200590:
- NVDAUSDT exists on Aster V3 futures public API.
- 281 one-minute bars on burned source date 2026-09-30.
- current source-gate spread snapshot ~1.2756 bps.

Frozen outcome sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude burned source date 2026-09-30
- 14:31–18:44 UTC.

Frozen rule:
- external = mean(Binance NVDAUSDT, Bitget NVDAUSDT) 1m return
- shock >=5 bps
- same-sign external-minus-Aster lag gap >=3 bps
- FOLLOW_EXTERNAL_CONSENSUS
- horizon 1 minute
- cooldown 1 minute
- exact timestamps, no forward fill.

PASS:
N>=30; >=12 signal sessions; mean>0; median>0; win>50%; both halves mean>0; exact one-sided binomial p<0.05.

Cost scenarios are 0, 1.8, 2, 3, 4, 5 bps round trip. Published RWA category fee is treated as provisional execution authority and must be pair/account verified before any live authorization.

No tuning, retrospective rescue, private endpoints, account reads, wallet actions, orders or live trading.
