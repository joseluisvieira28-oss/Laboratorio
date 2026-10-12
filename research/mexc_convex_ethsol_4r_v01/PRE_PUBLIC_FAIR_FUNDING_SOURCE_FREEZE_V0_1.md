# PRE-OUTCOME PUBLIC FAIR-PRICE & FUNDING SOURCE FREEZE — 2026-10-12

Experiment: MEXC-CONVEX-ETHSOL-4R-001; strictly additive SOURCE gate to existing design; not a new strategy, no trading or position authority.

Documentation source before probe:
- https://www.mexc.io/api-docs/futures/market-endpoints/get-funding-rate
- https://www.mexc.io/api-docs/futures/market-endpoints/get-fair-price (public fair_price GET)
- https://www.mexc.io/api-docs/futures/market-endpoints/get-funding-rate-history
- Risk limits are PRIVATE account endpoint and explicitly out of scope. Never call them.
- Earlier native venue historical funding was too short for 2021–2025; this probe does NOT attempt historical strategy replay.

Fixed instruments: ETH_USDT, SOL_USDT, no outcome-based dropping, ONE-SHOT GitHub Actions public GET only.
Allowed domain: contract.mexc.com; exact allowed GET:
1. /api/v1/contract/ping
2. /api/v1/contract/fair_price/ETH_USDT and /SOL_USDT
3. /api/v1/contract/funding_rate/ETH_USDT and /SOL_USDT
4. /api/v1/contract/funding_rate/history?symbol=<ETH_USDT|SOL_USDT>&page_num=1&page_size=1000 (source coverage only; no trading results).

For each JSON response require success=true/code=0 and valid data, HTTP <=2s, payload SHA256, start/receipt UTC ms, exchange timestamp positive, nonfuture and <=2s old for fair price & current rate; finite positive fairPrice, numeric signed fundingRate with bounded absolute magnitude <=1, collectCycle positive, nextSettleTime positive; history first page valid list (settleTime numeric, nonfuture), SHA and coverage timestamps. Do not assume next funding equals settled funding. If missing, stale or malformed, FAIL_CLOSED with exact reason; no SOURCE_GATE_PASS for missing instrument. Historical completeness, funding event valuation, mark/liquidation equivalence and future continuous data are NOT proved by one GET.
The first source gate can conclude PUBLIC_FAIR_FUNDING_SOURCE_PASS_DIAGNOSTIC only if BOTH current fair/rate and history sample validate, otherwise PUBLIC_FAIR_FUNDING_SOURCE_BLOCKED. In all cases: account risk tiers/maintenance & liquidation BLOCKED_PRIVATE_UNAUTHORIZED; no 4R economic forward, PnL or capital/live GO.

Preserve one JSON per run as immutable GitHub artifact with source SHA256 and fields, no secrets. No direct authenticated API, orders, accounts, wallet, private risk limit, no `main` merge, no Render, no 2026 protected holdout opening, no revision of original experiment design.
