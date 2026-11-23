# BINANCE-DIAMANTE-002 — Spot public microstructure + hypothetical execution-cost source gate
**Pre-data freeze: 2026-11-23 UTC. RESEARCH ONLY. NO TRADING.**
Branch isolated from `main`. This is a **one-off source / cost-feasibility probe**, not a trading strategy, not a historical L2 backtest and not PnL.

## Scientific question (not prediction)
Can we verify a fresh, **public anonymous Binance Spot orderbook** and recent aggressive-trade records, and quantify same-snapshot instantaneous market-order friction for specific hypothetical sizes **without claiming fills**?

## One-off scope frozen before looking at data
- Exact assets: `BTCUSDT`, `ETHUSDT`, `SOLUSDT`; Binance **Spot only**.
- **Exactly six public GETs** from `https://data-api.binance.vision`:
  - 3 `GET /api/v3/depth?symbol=<SYMBOL>&limit=100` (one per symbol)
  - 3 `GET /api/v3/aggTrades?symbol=<SYMBOL>&limit=100` (one per symbol)
- Sequential requests, once per asset, **no retries**, 10-second timeout, max 512 KB/response, server restrictions respected; **HTTP 451 => SOURCE_BLOCKED** (do not circumvent).
- Preserve raw JSON for each successful response with SHA256 + request-start/response-received UTC timestamps and monotonic duration, plus SHA256 of report and stdout diagnostics. No signed endpoints, account/user APIs, deposits, API keys or private web sockets.
- Rejection checks: status 200, valid JSON keys, `lastUpdateId>0`, strictly sorted positive bids/asks, no crossed book, valid Decimal prices and quantities, valid recent `aggTrades` IDs, sizes, prices, millisecond times and `isBuyerMaker` flag. No null-to-zero substitution.
- Don't claim the last 100 trades span a fixed minute, nor are aggTrades and book mutually timestamp-synchronous. Depth REST snapshot does **not** establish uninterrupted order-book reconstruction; no maker queue or fills.
- No historical depth archive assumed. `BINANCE-DIAMANTE-001 PR #372` Spot 1m integrity ≠ L2 history.

## Predeclared cost method
- Hypothetical **immediate buy followed by sell at the same depth snapshot**, quote-denominated entry sizes **100 and 1000 USDT** per symbol.
- Buy: walk *ask* levels until exact requested quote spend is exhausted; obtained base units = sum(quote_fill / ask_price).
- Sell: immediately walk *bid* levels for exactly those base units; gross proceeds = sum(base_fill × bid_price).
- If either side lacks enough depth for the size, report `INSUFFICIENT_DEPTH`; never extrapolate invisible levels.
- Fee scenarios: **0 bps per leg** (price/spread/depth cost only) and **10 bps per leg** (illustrative regular user 0.1%/trade, charged in quote notional on each side). **Not authenticated account fees**; rebates, BNB discounts and pair promotions unverified.
- `loss_usdt = buy_spend × (1+fee) - sell_proceeds × (1-fee)`.
- `loss_bps = 10000 × loss_usdt / (buy_spend × (1+fee))`.
- Depth and spread are **instantaneous static-book counterfactuals**, not realized slippage, actual trade PnL or return forecasts. This ignores queue competition, fees charged in other assets, order rejection, rapid book movement, market impact between legs and adverse selection. Do not infer strategy profitability or guaranteed exit.
- Output: best bid/ask, spread in bps, bid/ask 100-level available quote notional, hypothetical instant round-trip loss by size/scenario; last-100-trade buyer/seller aggressor counts only as auxiliary diagnostics, not a predictive signal. 3 assets must PASS both source types for overall `SOURCE_AND_COST_SNAPSHOT_PASS_ONLY`.

## Independence and stop criteria
No change/merge to `main`; preserve DIGUI-011 (#362), Binance 001 (#372), BTC10m NO_EDGE (#313), CPI/NFP NO_EDGE or SOURCE_BLOCKED closeouts; no replay of protected macro-event outcomes. No conditional production trigger, no cron schedule, no Render or Telegram integration. CI source-only PASS means live snapshot feasible on runner at that instant; NOT executable trading for a Swiss account.
Next gate if source PASS: authenticated-but-no-keys manual account fee/eligibility check by operator, and **a separate prospectively frozen** continuous WS depth-diff/snapshot bridge + independent capture+replay test, before any direction strategy. If SOURCE_BLOCKED, stop without mirror/region bypass.

Official public market-data endpoints: https://github.com/binance/binance-spot-api-docs/blob/master/faqs/market_data_only.md
Fee reference (not account-specific): https://www.binance.com/en-GB/support/faq/fee-structure-on-binance-115000429332
