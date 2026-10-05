# MEXC-NVDA-SOURCE-GATE-002 — SOURCE LEDGER

Date: 2026-10-05

## A. MEXC index architecture

### Proven dated regimes

1. 2025-07-21 / 2025-07-23 launch phase
Official MEXC launch material states Stock Futures were synchronized with U.S. stock-market hours and that the fair price was anchored to the latest price of the corresponding U.S. stock.
Sources:
- https://www.mexc.com/announcements/article/new-feature-mexc-to-launch-stock-futures-enjoy-0-fees-for-a-limited-time-in-the-u-s-stock-market-17827791526192
- https://www.mexc.com/announcements/article/new-stock-futures-listings-17827791526193

2. Effective 2025-09-20
MEXC explicitly announced that Stock Futures index components would no longer be based on underlying-stock prices and would instead use spot prices of ONDO U.S. stock tokens.
Source:
- https://www.mexc.com/announcements/article/stock-futures-all-new-upgrade-17827791530245

3. Current general MEXC index methodology
MEXC states index price is a weighted average of source prices; components/weights may change; delayed sources can be excluded; a source deviating more than ±1% from the median may be excluded when at least three sources are available.
Source:
- https://www.mexc.com/support/article/faq-on-index-price-fair-price-and-last-price-7950960183961

4. Current NVDA public contract snapshot already archived by MEXC_NVDA_001
The saved public contract/detail snapshot reports NVIDIA_USDT and an indexOrigin list:
[BINANCE_FUTURE, BITGET_FUTURE, BINANCETICKER, PYTH, KAIKO].
This is direct public MEXC API evidence preserved in the parent branch, but the labels alone do not prove active weights, exact source instruments, publication latency, or the date the prior ONDO regime ended.

### Missing
No official MEXC announcement/source was found that proves:
- the exact effective date of ONDO -> current multi-source transition;
- historical NVDA-specific constituent weights;
- exact source-instrument identifiers behind every current indexOrigin label through time;
- NVDA-specific fallback/staleness settings beyond the general FAQ.

Verdict A: SOURCE_PARTIAL.

## B. Nasdaq NVDA reference

### Official sources found

Nasdaq Basic:
- real-time Nasdaq BBO and Last Sale;
- available via Nasdaq Data Link;
- documented as a commercial/Premium product.
Sources:
- https://www.nasdaq.com/products/data/equities/nasdaq-basic
- https://data.nasdaq.com/databases/NB/documentation

Nasdaq Historical TotalView-ITCH:
- historical tick-by-tick order/trade transaction logs;
- exactly suitable scientifically for historical lead-lag;
- requires subscription/approval and is fee-bearing.
Sources:
- https://www.nasdaq.com/products/data/equities/nasdaq
- https://www.nasdaqtrader.com/TraderNews.aspx?id=dn2016-06

Nasdaq cloud Bars API:
- documented in the parent branch architecture addendum;
- requires authorization/provisioned service access;
- no free unauthenticated NVDA corpus was established.

### Rejected substitutes
Unproven third-party free bars, delayed web charts, or feeds without exchange/publication timestamp semantics do not satisfy the preregistered causal lead-lag gate.

Verdict B: SOURCE_BLOCKED for public/free causal lead-lag.

## C. NVDA share ↔ tokenized-stock rails

### Ondo NVDAon

MEXC listed NVDAON/USDT on 2025-09-03.
Source:
- https://www.mexc.com/announcements/article/mexc-to-launch-ondo-s-tokenized-stock-trading-pairs-on-spot-markets-2025-09-03-17827791529298

Ondo states:
- Ondo Stocks are fully backed by underlying shares plus cash in transit;
- tokens provide economic exposure to the underlying;
- they are total-return trackers;
- dividends are reinvested net of applicable withholding tax;
- splits/other corporate actions are reflected in the token;
- asset pages expose a Shares Per Token concept.
Sources:
- https://ondo.finance/ondo-stocks
- https://app.ondo.finance/assets/nvdaon

However, this review did not establish a public machine-readable historical NVDAon shares-per-token/multiplier series covering the full MEXC test period. Raw NVDAON/share price equality must not be assumed across corporate actions/dividend accrual.

### xStocks NVDAx / MEXC NVDAX

MEXC listed NVDAX/USDT on 2025-07-01.
Source:
- https://www.mexc.com/announcements/article/mexc-to-launch-xstocks-trading-pairs-on-spot-markets-2025-07-01-17827791525275

Backed/xStocks states:
- NVDAx is a tracker certificate for NVIDIA;
- underlying is NVIDIA Corp / NVDA;
- xStocks are 1:1 backed by underlying securities;
- dividends and stock splits are handled by rebasing/multiplier mechanics;
- the public xStocks API exposes corporate-actions and token multiplier/multiplierUpdates endpoints.
Sources:
- https://assets.backed.fi/products/nvidia-xstock
- https://xstocks.com/partner
- https://api.backed.fi/api-docs/

This makes NVDAX normalization technically recoverable, subject to retrieving the actual multiplier history for the test interval.

Verdict C: SOURCE_PARTIAL overall.
Reason: NVDAX mechanics/history are sourceable; NVDAon economic mechanics are proven but a time-versioned adjustment-factor series was not established here.

## Global implication

The causal chain NASDAQ -> token/index -> MEXC cannot be opened honestly under the public/free mandate because Gate B is SOURCE_BLOCKED, while Gates A and C remain PARTIAL.
