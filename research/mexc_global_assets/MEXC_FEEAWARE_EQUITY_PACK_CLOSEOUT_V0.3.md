# MEXC FEE-AWARE EQUITY PACK — CLOSEOUT V0.3

Date: 2026-10-04
Run: 37230806662
Branch: `mexc-feeaware-equity-pack-v0.3-prereg-2026-10-04`

Frozen rule for every asset:
- external shock >=20 bps
- lag gap >=10 bps
- FOLLOW_EXTERNAL_CONSENSUS
- horizon 1 minute
- cooldown 1 minute
- no grid search

Holm-Bonferroni FWER 0.05 across NFLX/BABA/GOOGL/ORCL.

## Results

NFLX:
- N=9, 8 signal sessions
- wins=3 / 9
- mean=-3.465793 bps
- median=-2.572678 bps
- thirds=+4.185954 / -8.758255 / -5.825079
- p=0.910156
- classification `FEEAWARE_UNDERPOWERED`

BABA:
- N=3, 3 signal sessions
- wins=3 / 3
- mean=+3.647208 bps
- median=+3.683580 bps
- p=0.125
- classification `FEEAWARE_UNDERPOWERED`

GOOGL:
- N=0
- classification `FEEAWARE_UNDERPOWERED`

ORCL:
- N=20, 11 signal sessions
- wins=13 / 20
- win rate=65%
- mean=+3.791656 bps
- median=+5.009339 bps
- thirds=+2.960035 / +4.223096 / +4.073034
- p=0.131588
- scientific eligible before Holm but not Holm-rejected
- classification `NO_EDGE_FEEAWARE`

Scientific survivors: 0.
Execution-scale survivors: 0.

Frozen verdict:
`NO_FEEAWARE_SURVIVOR_AT_FROZEN_V03_GATE`

Artifact SHA256:
`35cbdd4b184a4a9cff2fb750793eaf154024b6f070922af4fd1a4523cb3622d5`

Family conclusion:
raising the external-shock/lag thresholds to 20/10 bps does not produce a defensible execution-scale 1-minute edge in this frozen sample. Do not rescue by lowering thresholds after these outcomes.

No private endpoints, account reads, wallets, orders, exchange mutation or live trading were used.
