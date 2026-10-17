# CONVEX V03 — 4 STRICTLY CAUSAL HISTORICAL BINANCE L1 ENTRY CHECKS (2026-10-17)

**Source-only, 2023–2024 already-observed original V5 history.** Frozen before quote reads in `PRE_OUTCOME_L1_SOURCE_FREEZE_2026_10_17.md` (commit `3359db1`). Github Actions [39026315551](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/39026315551) **SUCCESS**. Twelve no-network regression tests PASS and a single frozen source runner recovered ONLY canonical original per-trade source artifacts from historical run 38432883246. All retrieved official daily ZIPs required original publisher SHA256 checksum; no exchange API, login, orders or 2026 holdout.

## Frozen 4 historical earliest BASE entries — every one, no selection by returns

| Original lane | Entry close/modeled-open date UTC | Last past quote age | Best ask | Quoted ask qty | Original modeled entry qty | Verdict |
|---|---|---:|---:|---:|---:|---|
| BNBUSDT 4h | 2023-11-01 16:05:00 | 249ms | 223.26000000 | 45.87 | 8.82249 | BOOK_QUOTE_CAUSAL_CANDIDATE |
| BNBUSDT 4h | 2023-12-17 08:05:00 | 286ms | 240.28000000 | 4.94 | 8.29827 | **TOP_OF_BOOK_SIZE_INSUFFICIENT** |
| SOLUSDT 1h | 2023-05-16 00:05:00 | missing prior quote on archive day | — | — | — | **SOURCE_NO_PRIOR_QUOTE** |
| SOLUSDT 1h | 2023-05-29 16:05:00 | 64ms | 20.46300000 | 408 | 104.79202 | BOOK_QUOTE_CAUSAL_CANDIDATE |

Among 3 fresh historical book quotes, ask vs original simulated entry (which includes BASE 2bps adverse slippage) differs by BNB 2023-11-01 **-1.99960008bps**, BNB 2023-12-17 **-1.58348486bps**, SOL 2023-05-29 **-1.51098702bps**. Negative means publicly quoted ask below original paper entry at that instant. This is **not** proof that a same-size taker order filled at ask, that missing levels provide additional liquidity, that earlier posted queue orders don't disappear, or that original exit/stop model was realistic.

Critical discovery: BNB 2023-12-17 best ask depth 4.94 BNB vs required modeled 8.298 BNB. Cannot infer full execution at top ASK, cannot replace missing depth with orderbook levels without historical L2. The SOL 2023-05-16 first candidate lacked same-day prior event; never backfilled the quote after entry. All 4 retained in denominator.

## Context, limitations and correct economics

- Source corresponds to **Binance USD-M** and SAME underlying as original V5 Binance signals, not MEXC/Kraken/OKX. It does not prove cross-venue portable performance.
- Original 8ALT frozen SOL1h 84 closes / BNB4h 28 closes across 3 years; 33 and 6 original BASE entry timestamps respectively occur in the fixed 2023-05-16 to 2024-03-30 bookTicker publication span. Full 39-entry source audit V03B separately frozen in `V03B_ALL_ELIGIBLE_PRE_RESULTS_FREEZE_2026_10_17.md`, never cherry-pick.
- BookTicker is L1 best bid/ask event only, not a 400-level L2 market snapshot or broker fill. Historic original fee/cost/funding/stop and overnight quote at exit remain unproven; 2026 OOS still sealed.
- SHA verified for each retrieved ZIP and `L1_CAUSAL_ENTRY` findings in Actions job logs / artifact ID `12098358985`.

**CONCLUSION: PUBLIC HISTORICAL L1 SOURCE CAUSAL JOIN PROVEN FOR 3/4 ORIGINAL HISTORICAL ENTRY EVENTS, FRESH BEST-ASK CAPACITY PROVEN FOR ONLY 2/4; NO FILL, NO NEW NET ALPHA, NO LIVE GO.**
