# MEXC LEVERAGED CASH-OPEN — PRE-OUTCOME FREEZE V0.9

Date: 2026-10-05
Status: FROZEN BEFORE OUTCOMES

Source gate run 37263663817:
- MUU_USDT / MUUUSDT: PASS
- MVLL_USDT / MVLLUSDT: PASS
- source date 2026-09-30 burned
- source artifact SHA256: f4243a0fc1ec294029d81ecf3a85d707d0ba2a20e35164313167ac1b0e24d4ce

Frozen sample:
- weekdays 2026-09-09 through 2026-10-02
- exclude 2026-09-30

Frozen rule:
- signal 13:29 UTC
- external = mean(Binance + Bitget)
- basis = 10000*(MEXC/external - 1)
- side = -sign(basis)
- no threshold
- entry MEXC 13:29
- exit MEXC 13:59
- horizon 30m

Scientific PASS:
- N>=15
- mean>0
- median>0
- win rate>50%
- both chronological halves >0
- exact one-sided binomial survives Holm across 2 assets, FWER 0.05

Operational:
- net after 12 bps >0 = fee-floor survivor
- net after 16 bps >0 = robust API-fee survivor

No tuning, post-outcome rescue, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
