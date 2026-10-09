# YT-AXIA-VAP-001 — TERMINAL SOURCE-ONLY ROBUSTNESS CLOSEOUT
Date: 2026-10-09
**Decision: SOURCE_GEOMETRY_ROBUSTNESS_FAIL / exact detector CLOSED.**
Economic outcomes: NEVER OPENED. No trading, account access, wallets, Render or main merge.

## Origin and scope
Public Axia creator case study: https://axiafutures.com/blog/footprint-strategies-you-can-apply-in-your-trading/
Original theme: micro double distribution, P-shaped volume at price, low-volume node, with additional DOM/market context. Our numeric two-peak 1bp BTC spot detector is solely a Crypto Lab adaptation, NOT a literal reconstruction of Axia's trading practice. Full original video transcripts were not independently verified.

Original pre-content price-grid/count freeze: `research/youtube_edge_mine/YT_AXIA_VAP_001_SOURCE_CENSUS_FREEZE.json`, commit `390b665a73f7df090a04ee1dec0ca94df9c69f18`.
Independent source robustness freeze: `research/youtube_edge_mine/YT_AXIA_VAP_001_G3_GEOMETRY_ROBUSTNESS_FREEZE.json`, commit `f0e6243f96c3c56079a990c577bc809596dbfa6e`.
Fixed: 5m signal-time BTCUSDT spot aggTrades, 1bp grid first-trade-anchored, 2 local volume peaks >=8% each, >=3 bins apart, valley <=35% of smaller peak, >=100 trades, >=8 occupied bins.

## Verified source gates
1. G2 metadata: [run 37930727761](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37930727761) — 10/10 public archive HEAD/checksum metadata, 10 synthetic tests PASS. No raw prices opened.
2. G2B prevalence: [run 37931269013](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37931269013) — three preselected 2022/23/24 official Binance Spot ZIP bodies verified by SHA256, 3,221,317 records, 385 shape bars (128/136/121), 401 eligible controls, 18 synthetic tests PASS. Source/count PASS only.
3. G3 independent source test: [run 37931809211](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37931809211) — three NEW untouched 2022/23/24 days SHA256 verified, 4,517,054 records, 304 shape bars (41/174/89), 531 eligible controls, 29 insufficient profile bars, 10 synthetic tests PASS.

## Frozen robustness verdict
- Predeclared phase stability: Jaccard>=0.70 after shift of half 1bp.
- Observed: base shape 304, shifted shape 304, **intersection 241 / union 367 = 0.6566757493**: **FAIL**.
- Matched source-only strata: 9 (minimum 6): PASS.
- Other source count/date/control gates: PASS.
- Placebo: permutation of observed bin volumes within each bar gave 3,524/6,680 positive (**52.75%**) vs original 304/835 eligible (**36.41%**). This is a descriptive source diagnostic, not a performance/predictive test.
- Last source artifact: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37931809211/artifacts/11616372064

## Scientific interpretation
Terminal `SOURCE_GEOMETRY_ROBUSTNESS_FAIL` for this exact lab detector BEFORE historical future-price outcomes. Do NOT soften the frozen 70% stability floor to 65%, retune bucket/bin widths or filters, pick favorable days, or open 2025/2026 to rescue it.
This is NOT `NO_EDGE` and DOES NOT invalidate the actual Axia discretionary approach. The source itself supports constructing traded volume by price, not proving a profitable signal.
No source-only/count pass is a trading or capital authority.

## Novelty and next direction
Unlike the existing `ABSORPTION-FAILED-AUCTION-001` scalar aggression/POC migration classifier, full volume-at-price distribution carries distinct raw observables. That is not evidence of *incremental predictive or economic* value.
Axia `JUMP` needs DOM pace/visible order-book response, not reconstructable from spot aggTrades alone; `ORDERBOOK-RESILIENCE-001` already failed source resolution for Binance ~30s bookDepth archives.
Seek a structurally different, economically forced-flow mechanism with a point-in-time data source and realistic pre-frozen cost model. No post-outcome adjustments under this closed identity.
