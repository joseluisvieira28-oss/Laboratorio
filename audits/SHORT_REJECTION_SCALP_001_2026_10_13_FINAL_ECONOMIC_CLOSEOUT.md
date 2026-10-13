# CRYPTO LAB — SHORT-REJECTION-SCALP-001 — FINAL ECONOMIC CLOSEOUT
**13 October 2026 (UTC).**

## Frozen economic hypothesis and source
New SHORT scalp separate from old LONG/SYMMETRIC SHORT CONVEX trend-capture families. Frozen **BEFORE** seeing any new outcomes at commit `d0fc72c83c89c868543cc8ab09cf1b9f45f6e513` in `research/short_rejection_scalp_001/PRE_OUTCOME_FREEZE_2026-10-13.md`. Source-semantics addendum `9c977e7e98a3a3aa5e5e0ab069f0949b8c05201a` also before outcomes. Unmodified eight predeclared USD-M perps ETH/BNB/SOL/XRP/DOGE/ADA/LINK/AVAX, homogeneous 2023-01 through 2025-12, Nov-Dec 2022 source warmup. Already-researched historical period = **NOT independent OOS**.

- **1h regime:** latest COMPLETED hour close under SMA200, hour SMA200 lower than SMA200 24 completed hours before.
- **5m sweep/rejection:** after previous 12 five-minute highs, current completed five-minute high sweeps above prior max, bearish close returns below that max, upper wick >= 50% of candle range. 1h state must already have closed at the signal timestamp; no future confirmation.
- **1m execution proxy:** SHORT at actual official 1m candle OPEN **one full minute AFTER** signal candle closes (one-second witness). One-slot independent paper account per symbol/scenario. 20% current cash notional, 1x, initial 10,000 USDT, no actual exchange borrow/margin confirmation.
- **Scalp exits:** +0.40% adverse SHORT stop, −0.80% downside TARGET (fixed 2R *gross*), 90 completed 1m minute time cap, gap at observed 1m OPEN, STOP_FIRST in ambiguous intraminute price bar. No manual alternative stop or hindsight retuning.
- **Cost BASE:** 8bps taker fee per side plus 2bps adverse modeled slip per side; STRESS 8bps taker and 5bps slip per side. Archived actual public historical funding rate, SHORT sign positive for positive rate, using 1m *market OPEN* settlement PRICE PROXY (not exact Binance mark). Independent 6h delayed-original-signal BASE placebo for each coin.
- Complete price/funding 5m, 1h source ZIPs (333,216 five-minute source bars, 27,768 one-hour audit bars, 3,288 funding events per symbol) and market 1m month ZIPs checked against Binance Vision publisher .CHECKSUM SHA256. All demanded monthly 1m archives full and contiguous, 34–36 observed 1m months per symbol. The independently published 1m and 5m archives had **historical price/volume revision differences for every symbol**, fully counted by the engine; thus reports are explicitly **SOURCE_REVISION_QUALIFIED**, not exact 1m-to-5m parity and not bid/ask-executable fills. The full period was never truncated to avoid inconsistent candles.

## Reproducible Actions validation
- Producer/market replay: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38446411938 — **SUCCESS**, all eight symbol jobs and 13/13 synthetic gates PASS.
- Original 24-arm read-only aggregation: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38446666193 — **SUCCESS**.
- Additional forensic CLOSED-TRADE cost decomposition (unchanged model, no outcome rerun): https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38447282210 — **SUCCESS**; immutable 24-arm CSV/JSON artifact https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38447282210/artifacts/11838681873.
- Exactly **24/24** fixed study arms, 8×(BASE,STRESS,6h delayed BASE), all replayed and reconciled, zero omitted profitable/losing arms. BASE closed trades across eight independent account ledgers = **10,903**.

## All eight AFTER-cost BASE / STRESS results, 2023–25 cumulative paper marked equity (not annual)
| Symbol | BASE return | STRESS return | Closed BASE | PF BASE | BASE win rate | BASE closed-equity DD | 6h delayed placebo BASE |
|---|---:|---:|---:|---:|---:|---:|---:|
| ADA | **-36.9098%** | -46.8138% | 1,336 | 0.4912 | 34.28% | -37.03% | -37.4619% |
| ETH | -39.7596% | -48.8014% | 1,321 | 0.3873 | 29.14% | -39.76% | -39.5968% |
| XRP | -40.5456% | -49.2320% | 1,283 | 0.3926 | 30.09% | -40.67% | -33.3692% |
| BNB | -42.0483% | -49.7215% | 1,218 | 0.2869 | 25.29% | -42.09% | -37.0788% |
| AVAX | -43.7622% | -54.3415% | 1,518 | 0.4566 | 31.69% | -43.76% | -42.9360% |
| DOGE | -44.6861% | -54.0035% | 1,373 | 0.3825 | 28.70% | -44.69% | -40.3665% |
| LINK | -45.3588% | -53.9020% | 1,441 | 0.4210 | 30.74% | -45.40% | -41.3460% |
| SOL | **-47.0461%** | **-55.8503%** | 1,413 | 0.3951 | 29.16% | -47.05% | -38.5944% |

Every asset and each of 2023, 2024, 2025 individually lost money in BASE and STRESS (yearly closed realized PnL). All 8 PF BASE well below 1 (0.287–0.491), despite huge sample count. 7 of 8 original BASE arms underperformed the simple delayed signal; ADA original marginally less negative (+0.55pp). Delayed control is a falsification, **not a statistical randomization test or a strategy candidate**. Trade counts and overlapping entry opportunities differ across controls.

## Why this is NOT just an overestimated-fees disaster
On the **unchanged closed BASE trade ledgers**, calculated per-trade economic components reconcile exactly:
| Coin | Closed market-price PnL after assumed adverse slippage, BEFORE fees & funding (USDT) | Closed fees USD | Funding model USDT | Static hypothetical closed PnL if ALL trading fees = 0 |
|---|---:|---:|---:|---:|
| ADA | -282.31 | -3,416.10 | +7.43 | **-274.88** |
| ETH | -684.22 | -3,303.64 | +11.89 | **-672.33** |
| XRP | -851.06 | -3,211.36 | +10.10 | **-840.95** |
| BNB | -1,158.67 | -3,022.92 | -23.25 | **-1,181.91** |
| AVAX | -691.62 | -3,688.84 | +4.24 | **-687.38** |
| DOGE | -1,167.75 | -3,310.66 | +9.80 | **-1,157.95** |
| LINK | -1,097.14 | -3,451.48 | +12.75 | **-1,084.39** |
| SOL | -1,370.72 | -3,336.26 | +2.37 | **-1,368.35** |

**All eight fixed closed ledgers are negative even when hypothetical fees are stripped out**. This is **static fixed-trade accounting** only, NOT a complete rebalanced zero-fee portfolio replay; the 1m adverse slippage is still assumed and historical equity sizing may change under zero fee. Therefore loss is due to insufficient actual SHORT price drift/capture plus heavy turnover/costs, not just commission. Market-price PnL itself (after slip but before fees/funding) is negative in 8/8. Under target +0.8% gross vs stop -0.4% gross and assumed round-trip BASE friction near 0.2%, idealized breakeven win rate is about 50% for fully reached barriers (time exits/gaps and funding change actual required rate). Observed 25.29%–34.28% are far beneath this benchmark. Reoptimizing TP/SL on the same years would be post-outcome rescue, not science.

## Explicit scientific decision
**EXACT V0.1 REJECTED — HISTORICAL_ECONOMIC_FAIL / NO FORWARD_RESOURCE_ALLOCATION / NO TRADING_AUTHORITY.** Do not place on Radar Fishing or arm auto-live. Archive and de-prioritize this fixed pair of signals, stops and timeframe; retain full negative ledgers for future false-positive audit. This does **NOT** prove that every conceivable SHORT scalp fails: an economically DISTINCT mechanism with new causal data and preregistration could be separately investigated, but no reason to continue parameter sweeps on the same 2023–25 outcomes.
The prior DOGE SHORT 1h, AVAX SHORT 4h, SOL LONG 1h and BNB LONG 4h are different swing/trend capture families and **are not invalidated by this scalp child**; none currently has independent OOS+execution permission. For user's economic goals, focus next on validating actual venue mark/funding and executable quotes for strongest preexisting distinct research family rather than endlessly optimizing this losing 90m scalp.

No live trading, orders, main merge, private API, wallets/accounts, Render deployment, spent funds, protected 2026 holdout, hindsight re-tuning or automatic future collector activation.
