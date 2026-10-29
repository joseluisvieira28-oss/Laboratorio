# Event Futures multi-asset source gate V0.1 — 2026-10-29
SOURCE ONLY / NO OUTCOMES / NO LIVE.

The user screenshot shows Event Futures listing labels BTCUSDT, ETHUSDT, SPCXUSDT, MLIUSDT and NVDAUSDT. Only the ETH 10-minute payout 80% UP/DOWN is visible; never apply that payout to other symbols.

The prior exact-product capture of 2026-10-03 found Event Futures internal contracts NVIDIA_USDT, SPCXSTOCK_USDT and MUSTOCK_USDT in PAUSE, and BTC_USDT and ETH_USDT in ONLINE, with time-variable direction-specific payouts. Those old states may have changed. The exact identity of MLIUSDT is not established; never silently treat it as MU, MUSTOCK or another market.

Freeze scope before market data:
- Reuse previous unauthenticated Chromium passive capture of exact MEXC Event Futures product detail, all symbols, states, cycles, payouts with raw hash. GET-only/no private/order/account methods.
- Query public MEXC standard futures INDEX Min5 candles for exactly BTC_USDT, ETH_USDT, NVIDIA_USDT, SPCXSTOCK_USDT and MUSTOCK_USDT, in 2026-10-22 through 2026-10-24 UTC EXCLUSIVE. This period is discovery only. Do not open April/September protected history or payout outcomes.
- Validate hash, HTTP 200, source schema, 576 expected 5min slots, positive finite prices, aligned timestamps and count gaps. Bar coverage >=80% is basic source gate only; no imputation, proxy price != executed Event Futures price.
- MLIUSDT remains UNKNOWN_IDENTITY unless the public product configuration or authoritative symbol map establishes an identity; do not guess a contract or include it in backtests.
- All product states/payouts are as-of capture, NOT historical payouts for 2026-10-22.
No outcome/return/strategy/EV test at source gate. No trading, orders, balances, keys, private endpoints, wallets, spending, main merge or live activation.
