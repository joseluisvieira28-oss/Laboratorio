# MEXC GLOBAL-ASSET — INTRADAY LARGE-SHOCK CATCH-UP
## PRE-OUTCOME FREEZE V1.1

Date: 2026-10-05
Status: FROZEN BEFORE OUTCOMES

Source authority:
- source gate run 37282772060
- artifact ID 11332209029
- report SHA256 `9f38273c7ed4673bd4da05c2a4268412b76e052fd7570d9da4bd00ec7a7fb61c`
- artifact ZIP SHA256 `961f3214ce7de25d1dc0e473f5f5f8412bd647b1529d1bd09af224676f2d271f`
- 35/35 inherited MEXC + Binance + Bitget identities passed full-session 1m source coverage on burned date 2026-09-30.
- 2026-09-30 is excluded from outcomes.

Economic rationale fixed before outcomes:
The known regular-session MEXC follower effect is only ~3–6 bps gross and cannot survive standard API fees. This family therefore requires a materially larger information shock and a materially larger observed target lag before entry.

Frozen sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude 2026-09-30
- scan U.S. regular-session closed timestamps from 13:45 through 19:55 UTC

Frozen signal:
- lookback = 15 minutes
- Binance and Bitget 15m returns must have the same sign
- each leader must move at least 50 bps absolute
- mean external 15m move must be at least 60 bps absolute
- MEXC return measured over identical closed timestamps
- lag gap = external mean return - MEXC return
- sign(lag gap) must equal sign(external)
- abs(lag gap) >= 25 bps
- direction = FOLLOW_EXTERNAL_CONSENSUS
- enter at the MEXC close available at the signal timestamp
- exit exactly 5 minutes later
- no information after entry is used by the signal

Dependence control:
- all qualifying assets at the same timestamp are equal-weighted into one event basket
- after one event basket is admitted, a global 15-minute cooldown suppresses every later timestamp inside that interval
- all admitted event baskets on the same UTC date are then equal-weighted into one daily basket
- the daily basket is the scientific unit

Scientific PASS:
- >=20 admitted event baskets
- >=8 triggered dates
- mean daily gross >0
- median daily gross >0
- winning-day rate >50%
- both chronological halves of daily basket means >0
- exact one-sided binomial p<0.05 across triggered days

Costs:
- report 0 / 12 / 14 / 16 / 20 bps round trip separately
- ROBUST_API_FEE_SURVIVOR requires scientific PASS plus mean and median daily net >0 after 16 bps

One frozen hypothesis only:
- no threshold grid
- no horizon grid
- no per-asset tuning
- no retrospective rescue
- no post-outcome tuning

Safety:
- no private endpoints
- no account reads
- no orders
- no wallets
- no exchange mutation
- no live trading
