# MEXC MULTI-EQUITY CASH-OPEN BASIS-FADE — CLOSEOUT V0.2

Date: 2026-10-04
Run: 37231185119

Frozen rule:
- observable signal 13:29 UTC
- basis = MEXC / mean(Binance, Bitget) - 1
- direction FADE_BASIS
- no basis threshold
- horizon 30 minutes
- six assets
- Holm-Bonferroni FWER 0.05

Results:
- AAPL: N=17, 11 wins, mean +20.869444 bps, median +18.487044 bps, halves +37.677596 / +5.928864, p=0.166153, no Holm
- MSFT: N=16, 10 wins, mean +26.448055 bps, median +33.156030 bps, halves +8.552902 / +44.343208, p=0.227249, no Holm
- META: N=17, mean +10.072378 bps, median -2.739201 bps, unstable halves, no Holm
- TSLA: N=16, mean -11.610754 bps, no edge
- PLTR: N=17, mean -43.594220 bps, no edge
- AMZN: N=17, mean -10.675532 bps, no edge

Scientific survivors: 0.
Execution-scale scientific survivors: 0.

Frozen verdict:
`NO_CASHOPEN_BASISFADE_SURVIVOR_AT_FROZEN_V02_GATE`

Artifact SHA256:
`a77d686e7ba1d8d6c6a38e5272d3d01c5ea15c81d0e3028fd8787574c1778ce4`

AAPL and MSFT show economically large gross observations but did not pass the frozen statistical gate and must not be promoted from this sample.

No threshold rescue, horizon switching, asset cherry-picking, private endpoints, account reads, wallets, orders, exchange mutation or live trading were used.
