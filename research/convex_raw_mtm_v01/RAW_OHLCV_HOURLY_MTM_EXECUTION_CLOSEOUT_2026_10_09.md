# BTC Convex V5 — raw 2021-2025 full OHLCV, funding and hourly MTM risk closeout (09 Oct 2026)

## VERDICT
- **RAW_HISTORIC_DATA_AND_ORIGINAL_TRADES_REPRO: PASS** (3/3 ETHUSDT, SOLUSDT, BNBUSDT).
- **SHARED_LOW_RISK_HOURLY_MARKED_RISK_AUDIT: PASS** (synthetic risk model, not observed broker execution).
- **LIVE_EXECUTION_EXACT_BBO_AND_ORDER_FILLS: UNVERIFIED**. No micro-live GO, no order/wallet/API account action, no main merge.
- All 2021-25 scientific outcomes were already known; this exercise is exact raw-data reproduction, NOT fresh OOS/2026.
- 13-symbol generalization FAIL remains unchanged and is not weakened by local first basket audit.

## Canonical executed experiment and immutable source
Original official Parent experiment pinned to actual run 35918769969, original commit `8832eb8e8fe95e7914d3fe8628b0398d9695ad4a`, source script blob `49e2bafd2e487352db24f2a812e936372a2cb1ff`; unchanged `load_symbol` + `simulate` original function definitions were used against newly retrieved Binance Vision OHLCV, exact official historic mark and funding.
The original canonical economic ledger artifact 10775714534 `CROSS_ASSET_COST_VALIDATION_V0.1.json` was independently restored and checked: exact immutable source SHA of all downloaded OHLC/mark/funding transport pages vs original `manifest_entries`, 43,824 hourly market bars per asset 2021-01-01→2025-12-31, trade by trade same timestamps, entry price, exit price, PnL, fees, funding, slippage, original MTM DD and original result sign. No rounding rescue/source substitution.
Successful workflow GitHub Actions **37916963862**, SHA **20c736bbf4fa2830100ef67c79ed395c4bcfb276**, artifact **11611165132**, name `btc-convex-raw-ohlcv-mtm-economic-v01`. Dynamic source/funding reconciliation max residual **0.0 USDT** at reported precision.

## Shared 10,000 USDT capital account, same 1% planned-risk cap, 3 concurrent max
Two original frozen cost layers: BASE=10bps fee+2bps slip per side, STRESS=10bps fee+5bps slip per side, original per-timestamp historic Binance funding. Position sizing risk 0.25% or 0.50% of realized account at new entry, planned 4.24% stop+cost risk denominator, no leverage rescue. The original historical signal and original stop/trailing/gap fill assumptions are unchanged.

| 2021-2025 cumulative result | BASE 0.25% | BASE 0.50% | STRESS 0.25% | STRESS 0.50% |
|---|---:|---:|---:|---:|
| Completed positions | 365 | 221 | 366 | 223 |
| Skipped signals due to portfolio risk cap | 0 | 144 | 0 | 143 |
| Realized net return over five years | +34.5961% | +20.0803% | +33.6847% | +16.9500% |
| Maximum CLOSED-only capital DD | -6.9035% | -13.4996% | -7.0236% | -13.8257% |
| **Maximum hourly CLOSE MTM DD** | **-8.6650%** | **-15.9596%** | **-8.8029%** | **-16.2822%** |
| Hourly-close liquidation-cost-adjusted MTM DD | -8.6480% | -15.9564% | -8.7817% | -16.2783% |
| Max losing streak | 19 | 20 | 19 | 20 |

NOTE: liquidation-adjusted DD need not be numerically more negative than unadjusted DD because its running peak can change. Both show hourly CLOSE observations only and assume same original fixed slip; they **do not bound intrahour trade/liquidation-risk drawdown** or exact marketability.

Raw audit also classified **18 same-hour entry-stop exits** and **2 STOP exits at 1h OPEN proxy**, per reproduced cost layer. The latter is NOT exact quantified stop gap severity without independent intrabar events/order receipts. Position risk cap denied 144 of 365 BASE first-basket trades at 0.50%, so higher per-trade planned risk did not improve historical net equity. 0.25% case had 29,548 completed bars with open risk, confirming closed-only DD was insufficient.

## What this SUCCESS proves—and does not
**Proves:** raw source byte hashes match preserved original 2021-25 receipts; original rule and funding replay can be reproduced; 0.25% risk-shared ETH/SOL/BNB portfolio retained +34.60% after original modeled costs and -8.67% hourly-close MTM DD.
**Does not prove:** all within-hour maxima or 1m stop chronology, true point-in-time MEXC order-book BBO/depth, realistic market-order fills/liquidity or exchange min contract, funding parity, account-specific fees, market transfer, and future expected net profit. TradingView supplied PnL was previously inflated in earlier diagnostics; our source is the original *causal bar* runner, not hindsight chart replay. 2026 data were not opened.

## Verified separate venue source gate
- Binance official data archives https://github.com/binance/binance-public-data — include historic klines/trades/aggTrades, but not MEXC point-in-time order book evidence for original entries.
- MEXC API Futures official current taker **0.08% per side** effective Jun 1 2026, maker **0.06% per side**; 16bps taker-taker commission RT **plus** spreads/slippage and funding. https://www.mexc.com/en-GB/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742
- Original 10bps fee per side is an explicit conservative Binance-model research assumption, not evidence of actual MEXC settlement fees or executable BBO. Transplant cannot be classified live net edge.

## Next economically relevant gate
Historical 1m (or tick) source check for intrahour stop gaps and earliest possible first touch, still NOT bid/ask executed fill. If immutable data insufficient, close as SOURCE_BLOCKED, preserve raw hourly PASS. For true live GO, separately establish historical/exchange executable quote and order sizing evidence before any capital authority.
