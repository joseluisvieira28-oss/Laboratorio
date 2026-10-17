# PRE-SOURCE FREEZE — KRAKEN PUBLIC 2023–25 HISTORICAL ANALYTICS FEASIBILITY V0.1

17 OCT 2026 UTC, independent public SOURCE-ONLY research; no prices/PnL calculations, no full historical backtest, no protected 2026 holdout, no private requests/accounts/order APIs, no capital, no execution.

## Fixed sources and exact probes before response inspection

Kraken official docs: https://docs.kraken.com/api/docs/futures-api/charts/market-analytics . Source endpoint `GET https://futures.kraken.com/api/charts/v1/analytics/{symbol}/{type}?since={sec}&interval=86400&to={sec}`.
ONLY symbols `PF_SOLUSD` and `PF_BNBUSD`.
ONLY analytics types `spreads` and `funding`.
ONLY fixed UTC five-day windows beginning 2023-01-03, 2023-12-03, 2024-06-03, 2025-06-03; 2 symbols x 2 types x 4 windows = **16 anonymous GET requests maximum**.
No retries/rotating source, no proxy/region bypass. Reject non-200/invalid-schema/gaps. Never backfill or infer historical fills. Save only SHA256 of raw HTTP bytes, response code, byte length, returned timestamp row count and covered UTC date bounds. Never publish raw historical economic series or mine for favourable dates.

Kraken official contract launch source: https://support.kraken.com/ch/articles/4844359082772-linear-multi-collateral-derivatives-contract-specifications `PF_SOLUSD` 2022-03-22; `PF_BNBUSD` 2023-11-22. The 2023 January BNB check is explicitly an **ineligible prelisting negative control** and MUST be classified `PRE_LISTING_INELIGIBLE` regardless of transport response. Do not count it as a source failure that can be remediated.

### Outcomes and scientific interpretation

- HTTP accessible with nonempty supported timestamps for a fixed postlisting window -> `SOURCE_DATE_COVERAGE_CANDIDATE`, NOT executed price, actual quoted 1m/5m book, exact funding cashflow, direct broker fill or trading edge.
- Empty, HTTP error, parsing failure -> `SOURCE_BLOCKED_OR_EMPTY` with literal HTTP/error class; no source substitution.
- Any 2023–25 source availability -> only a future source gate to check licensedness, instrument funding semantics and point-in-time data before any venue historical replay.
- 2023 before BNB listing -> `PRE_LISTING_INELIGIBLE`; do not credit it as Kraken hypothetical.
- No access to accounts, no expenses, no ex post threshold selection, no main merge, no Render, no software trading authority.

Even 16/16 hypothetical transport successes are **SOURCE FEASIBILITY ONLY / NO ECONOMIC OOS / NO LIVE GO**.
