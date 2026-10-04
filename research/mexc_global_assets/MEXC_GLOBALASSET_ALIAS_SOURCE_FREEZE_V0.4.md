# MEXC GLOBAL-ASSET ALIAS SOURCE GATE V0.4

Date: 2026-10-04
Status: SOURCE-ONLY / PRE-OUTCOME

The explicit MEXC target -> Binance/Bitget ticker aliases are frozen in `MEXC_GLOBALASSET_ALIAS_MAP_V0.4.json` before any V0.4 returns or PnL are computed.

Verification date: 2026-09-30.
This date is burned from later outcome tests.

Source PASS requires complete MEXC + Binance + Bitget 1-minute transport around 14:30–19:00 UTC.

Already-open outcome assets NVIDIA_USDT, TESLA_USDT, MUU_USDT and MVLL_USDT are excluded.

Source availability may select candidates. No return, signal, direction, win/loss or PnL may select candidates.

Any later outcome test must apply the same pre-frozen 5/3/1m FOLLOW_EXTERNAL_CONSENSUS rule to ALL source-pass candidates and control multiplicity across the full source-pass family.

No private endpoints, account reads, orders, wallets, exchange mutation or live trading.
