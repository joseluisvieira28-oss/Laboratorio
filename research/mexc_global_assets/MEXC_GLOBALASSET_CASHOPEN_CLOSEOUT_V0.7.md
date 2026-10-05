# MEXC GLOBAL-ASSET CASH-OPEN V0.7 — CLOSEOUT

Run: 37263391190
Date: 2026-10-05

Frozen family:
- 35 source-pass assets
- 13:29 UTC signal
- 30m MEXC basis fade
- no threshold
- Holm-Bonferroni FWER 0.05 across all 35 assets

Verdict:
`NO_CASHOPEN_SURVIVOR_AT_FROZEN_V07_GATE`

Counts:
- scientific PASS: 0/35
- net >12 bps survivors: 0/35
- net >16 bps survivors: 0/35

Large gross but non-promoted examples:
- ARMSTOCK_USDT: N17, 11 wins, mean +144.326 bps, p=0.166153
- QCOMSTOCK_USDT: N17, 12 wins, mean +88.827 bps, second half negative, p=0.071732
- SMCISTOCK_USDT: N17, 11 wins, mean +75.818 bps, p=0.166153
- COINBASE_USDT: N17, 10 wins, mean +67.233 bps, p=0.314529
- JPMSTOCK_USDT: N17, 14 wins, mean +51.973 bps, p=0.006363, but fails Holm cutoff 0.001429

These assets may not be retrospectively promoted or rescued on this dataset.

No parameter tuning, retrospective OOS, account reads, private endpoints, orders, wallets, exchange mutation or live trading.
