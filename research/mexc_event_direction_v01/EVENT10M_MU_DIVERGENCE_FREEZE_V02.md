# EVENT-10M MU V0.2 — MICRO CROSS-SOURCE DIVERGENCE HISTORICAL PILOT FREEZE
Date: 2026-10-29. Pre-outcome freeze. Parent source gate V0.1 GitHub Actions run #40905532432 PASS 40/40 aligned minutes on both 2026-10-26 and 2026-10-27. Only MU / MUSTOCK_USDT. NVIDIA separate project, SPCX not Nasdaq stock, MLIUSDT unresolved and excluded.

## Source identity locked
Exactly one Yahoo (unofficial MU chart 1m) GET 2026-10-26T00Z..2026-10-28T00Z, response SHA256:
9bbdf96057afe5d3b79a6dfa873d3b42e8b790ff7d8515c9cc32ed5e619b0efb
Exactly two MEXC standard Futures INDEX Min1 GET (same windows as V0.1 source proof):
2026-10-26 SHA256 69e65cd0839b1f4159a1f7f4ed24db028e23c2979be9d3e573d25cbcf64e372e
2026-10-27 SHA256 8895ef6740917cf4960ba4fd478db61e0dec0cce56873dc90e45401113394fa9
Fail closed if raw hashes differ or source schema fails. No substitution/retuning. Yahoo's unofficial chart may contain time-varying JSON metadata; full-body hash mismatch would block, NOT allow retroactive relabeling.

## Hypothesis, algorithm and match
MEXC Event Futures hypothetical direction only. Decision local America/New_York 09:40, 09:50, 10:00, 10:10 and 10:20 on each of the TWO days. Ten scheduled slots total, nonoverlapping 10-minute horizons.
At each t, source MU exchange stock 1m CLOSE[t-3m] minus CLOSE[t-5m] and MEXC index OPEN[t-3m] minus OPEN[t-5m]. Both are at least 2 minutes old before decision. No lookahead of MU candle at t. No threshold: sign only, equal means abstain. Only when both signs NONZERO AND OPPOSITE, forecast the MU stock sign for MEXC index direction over next 10 minutes; agreement => abstain. We must log eligible/abstention/missing as separate counts.
Target price proxy MEXC INDEX OPEN[t+10m] - INDEX OPEN[t]. WIN if forecast sign matches, LOSS otherwise, TIE if equal. This is NOT actual executed Event Futures order openPrice/settlement. No historical real payout, live source availability or stock-price receipt-time proof.
Compare on exact same triggered decisions with fixed baselines ALWAYS UP, ALWAYS DOWN and index momentum direction. Include both days irrespective of performance.
Payout sensitivity symmetric q=0.80 and 0.85 per win (lose -1/tie 0). As-of 29 Oct q cannot be assigned to 26/27; no actual economic edge claim.
Earlier previous tests opened October 26/27 index prices for other rules, so this is NOT untouched OOS and n<=10. Even positive results cannot be promoted or selected for live/forward without separate as-of collector + novel independently timestamped samples + payout/settlement matching.
No protected September 2026, NVIDIA, SPCX, MLI, orders, private API, account, paid source, main merge or live trading. Failed previous studies remain closed.
