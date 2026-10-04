# BINANCE ↔ BITGET STOCK LEAD-LAG V0.1 — CLOSEOUT

Date: 2026-10-05
Branch: `binance-bitget-stock-leadlag-v0.1-prereg-2026-10-05`
Run: `37239207816`

## Frozen evidence

Source authority:
- source-only run `37238930919`
- burned source date: 2026-08-14
- source artifact SHA256: `6300d91d8b7bdef8c201e1589e8f35a29e660f192ca7a99969374ea767b01d43`

Outcome family artifact:
- artifact ID: `11317135028`
- SHA256: `8ff31989d819783091bccac08f73936cfd7c942f19c23e02205c8c51d0171358`

Frozen outcome window:
- 2026-08-17 through 2026-09-04
- 15 weekdays

Frozen family:
- 34 source-valid assets
- two routes per asset
- 68 total asset-route tests

Frozen signal:
- leader shock >= 5 bps
- lag gap >= 3 bps
- sign(gap) = sign(leader return)
- FOLLOW_LEADER
- horizon = 1 minute
- cooldown = 1 minute
- no parameter tuning by asset or route

Multiplicity:
- Holm-Bonferroni FWER 0.05 across all 68 tests

## Family verdict

Scientific PASS:
- 9 / 68

Maker-only fee survivors:
- 4 / 68

Hybrid maker-taker fee survivors:
- 0 / 68

Taker-taker fee survivors:
- 0 / 68

Overall verdict:
`MAKER_ONLY_FEE_SURVIVORS_FOUND__FILL_MODEL_REQUIRED`

All four fee survivors occur in the same economic direction:
`BINANCE_LEADER__BITGET_TARGET`

No fee-surviving reverse route was found.

## Frozen current fee authority

Bitget target:
- maker-maker round trip: 4 bps
- maker-taker: 8 bps
- taker-taker: 12 bps

Binance TradFi target:
- maker-maker: 0 bps
- maker-taker: 4 bps
- taker-taker: 8 bps

## Four maker-only survivors

### HOODUSDT
- route: Binance leader -> Bitget target
- N = 1148
- wins = 680
- win rate = 59.233449%
- mean gross = +5.870005 bps
- median = +3.668056 bps
- chronological thirds = +6.598813 / +5.483117 / +5.529987 bps
- exact binomial p = 2.122270e-10
- Holm cutoff = 0.000746269
- net after maker-maker = +1.870005 bps
- net after maker-taker = -2.129995 bps
- net after taker-taker = -6.129995 bps

### COINUSDT
- route: Binance leader -> Bitget target
- N = 986
- wins = 600
- win rate = 60.851927%
- mean gross = +5.604399 bps
- median = +4.185348 bps
- chronological thirds = +7.667211 / +5.862250 / +3.290007 bps
- exact binomial p = 4.895130e-12
- Holm cutoff = 0.000735294
- net after maker-maker = +1.604399 bps
- net after maker-taker = -2.395601 bps
- net after taker-taker = -6.395601 bps

### ARMUSDT
- route: Binance leader -> Bitget target
- N = 923
- wins = 517
- win rate = 56.013001%
- mean gross = +5.279821 bps
- median = +2.168805 bps
- chronological thirds = +6.456052 / +4.712537 / +4.674693 bps
- exact binomial p = 0.000144664
- Holm cutoff = 0.000806452
- net after maker-maker = +1.279821 bps
- net after maker-taker = -2.720179 bps
- net after taker-taker = -6.720179 bps

### AAPLUSDT
- route: Binance leader -> Bitget target
- N = 86
- wins = 71
- win rate = 82.558140%
- mean gross = +4.452527 bps
- median = +3.875310 bps
- chronological thirds = +4.397731 / +4.217040 / +4.740921 bps
- exact binomial p = 3.538029e-10
- Holm cutoff = 0.000757576
- net after maker-maker = +0.452527 bps
- net after maker-taker = -3.547473 bps
- net after taker-taker = -7.547473 bps

## Interpretation

The cross-venue asymmetry is directional in this frozen window:
Binance leads Bitget strongly enough for four asset-route pairs to remain positive after the current Bitget maker-maker fee schedule.

None survives a maker-taker assumption.

Therefore the next blocker is not fee level alone; it is passive execution feasibility:
- post-only fill probability;
- queue position;
- spread;
- latency;
- adverse selection;
- cancellation/replace behavior;
- one-minute exit feasibility.

The same outcome window MUST NOT be used to tune the passive execution model after observing these four survivors.

A new execution model must be frozen before any new microstructure outcomes are opened.

No live trading, orders, account reads, private endpoints, wallets or exchange mutation were used.
