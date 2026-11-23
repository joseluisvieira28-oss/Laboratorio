# BACKES-DIAMANTE-002 — BTC vs ETH economic rotation, no trading
Frozen on **2026-11-23**. Historical close **2026-11-22 UTC**. This is an **independent Crypto Lab test** derived from public discussion of ETH/BTC rising lows, NOT the proprietary strategy of Augusto Backes.

## Data and controls
- Binance Spot official ZIP archives: https://github.com/binance/binance-public-data; 1d candles BTCUSDT, ETHUSDT and ETHBTC, 2018-01-01..2026-11-22 UTC.
- ZIPs stored temporarily by runner; report artifact preserves source URLs, byte lengths and SHA256 for every archive. Zero tolerance for missing days, duplicates, invalid timestamps/price and massive ETHBTC cross-rate mismatches.
- Weekly Monday–Sunday closed candles; signal after close on Sunday, position at following Monday opening. The last Sunday is valued at its closing price; initial acquisition cost included; terminal liquidation cost not charged.
- **Rotation signal:** ETHBTC swing low at week j is the minimum of 3 full weekly lows on each side; only known at the close of week j+3. At completed week t, choose ETH for week t+1 only if latest two confirmed swing lows are ascending AND ETHBTC closing price exceeds close t−4; otherwise choose BTC. 100% unleveraged spot.
- **Benchmarks:** 100% BTC hold, 100% ETH hold, and 50/50 BTC/ETH weekly rebalance. Mark-to-market in USDT at Binance Spot open/close prices.
- **Costs:** 5/10/20/35/100 bps cost per direct ETHBTC swap or initial acquisition, incorporating hypothetical fee + slippage; two-leg (via USDT) stress at 10/35bps. These are **modelled scenarios** not verified fees for the user's account.
- **Evaluation:** exploratory 2018–2022; validation-like 2023–2024; retrospective untouched-by-code-window 2025–2026-11-22; and all-period diagnostics. Results: net total return, CAGR, maximum drawdown, switch count, deterministic 8-week block bootstrap 95% interval (2,000 replications) of weekly active excess against each benchmark.
- **Strict distinction:** hypothesis was conceived in November 2026; ALL historical periods are retrospective research, even if no explicit tuning takes place. Cannot claim truly prospective edge from 2025–26 results.
- **Gate:** SOURCE_BLOCKED if any archive missing or invalid; ECONOMIC_NO_GO if rotations fail after stress/benchmarks; INCONCLUSIVE if sparse signals/uncertainty; CANDIDATE_ONLY if stronger than each benchmark and robust CI across periods and costs, requiring prospective replication. No live approval.
- **Safety:** read-only download, Python standard library, no API keys, trades, transactions, accounts, subscriptions, paid APIs, messaging, deployment or trading automation.
