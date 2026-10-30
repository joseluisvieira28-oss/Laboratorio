# CRYPTO LAB — BTC Event Futures 10m SINGLE HYPOTHESIS
## Read-only source + prospective paper custody engineering CLOSEOUT — 30 October 2026

**FINAL VERDICT: FOUR_LEG_CAUSAL_SOURCE_PASS, FUTURE_PAPER_PIPELINE_SYNTHETIC_PASS, ZERO REAL PAPER FORECASTS, ZERO 10M MARKET OUTCOMES, NO ECONOMIC EDGE CERTIFIED, NO LIVE GO.**

### Why this study matters
One and only one 10m BTC hypothesis: frozen V0.3 orderbook pressure difference between independent OKX SPOT and MEXC FUTURES. Three pre-decision orderbook pairs 4-8s apart, all three OKX top5 notional imbalances >=+0.25 against all three MEXC opposite <=-0.25 (or mirror for DOWN); else ABSTAIN. Strict public payout within 10sec and MEXC INDEX within 2sec; Nov1–30 UTC 10-minute decisions seconds20–40. **No threshold/asset/selection tuning** after source or market outcomes. Ethereum deliberately excluded from this single hypothesis.

### Real 30 October source proof — completed
[GitHub Action #41096454537](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41096454537), initial preregistration/freeze commit b271f61f4db5545139becaf3abe7e5895bfea0ac. GitHub artifact **12996537229**, ZIP SHA256 **a49052bce9e0ce8d7ba216bfcc00a5b9ca9ff5d474a06c591398b5553d1b567d**, uploaded 2026-10-30T17:10:54Z. Archive contains **nine files**: 3 raw OKX books, 3 raw MEXC Futures books, the anonymous exact public MEXC Event Futures product detail JSON, the MEXC standard futures index JSON and signed source-only receipt. Original raw HTTP body SHA256 receipts preserved, no login, non-GET and potentially sensitive browser routes blocked, no account/order/position/private endpoint.
- Single observation 2026-10-30T17:10:53.023Z: exact MEXC Event Futures BTC_USDT **10m ONLINE contractId 10**, dynamic **qUP=0.70 / qDOWN=0.70**, product response received 5.203s before sampled as-of timestamp, raw SHA256 c18613c02caa83fe3fe236ec9d3e6a7b1e050b161cbfc126b0bc7e45f1e1ce9e.
- Public BTC standard Futures indexPrice=77199.4, source server-to-local age **509ms**, raw SHA256 a7b0a1276d0ea76a1c6db0f9e68b93d14fe277f2edb4fdc7d69160bdf872db15. This is not an Event Futures server-assigned order opening/settlement quote.
- THREE independent OKX and MEXC top-of-book source receipt pairs were captured. All four as-of gates **PASS**: three orderbooks, final orderbooks <=2seconds, payout <=10seconds, MEXC public index <=2seconds. Entire source probe completed without any direction or target-return label.
- **Economic arithmetic:** point-in-time BTC q=.70 breakeven strictly above 1/1.70=**58.8235%** non-tie winners, before further real costs. On two earlier Oct30 captures BTC q=.80 (~55.56% threshold). Dynamic q must be captured for every future decision. Random symmetric 50% directional win rate at q=.70 would yield -0.15 unit EV per unit staked (before costs). Payment q=.70 is not permanent, not linked to any backtest event.

### Frozen November-only paper chain, NOT ACTIVATED
Added V0.5 future-only one-shot paper script:
1. Pre-declared aligned UTC 10m boundary Nov1–30, sample at roughly seconds12/17/22, exact-three-book pairs, anonymous exact BTC 10m payout and public index with original SHA.
2. Run **unchanged** V0.3 model strictly at UTC second20–40, no prediction if any source stale or if outside future Nov. ABSTAIN is allowed; no forced direction.
3. Prepare immutable `decision.json` plus eight original raw source responses. **Before any expiry query**, GitHub Actions artifact upload must complete; independently re-download ZIP, verify GitHub-server `created_at` before the expiry, exact ZIP SHA256, all eight raw body SHA256, original decision bytes, producing workflow repo/run, and **re-run V0.3 prediction** to check direction. Otherwise no outcome query. Github UTC metadata at seconds precision permits only <=999ms truncation before decision (not timestamp forgery).
4. For qualified UP/DOWN ONLY, after independent artifact custody, first public MEXC BTC_USDT INDEX WebSocket frame with server timestamp at/after decision+600000ms and <=5seconds, locally received after server and within <=5seconds. Else no-sample/blocked. Record only **INDEX SHADOW** WIN/LOSS/TIE using observed payout; actual Event Futures settlement parity and PnL **unproven**. Never submit exchange orders/trade.
5. For ABSTAIN, **never open an expiry market result**. Both source and expiry receipts have fail-closed outcomes.

**GitHub Actions one-shot workflow is DORMANT**: `.github/workflows/btc-event10m-paper-one-shot-dormant-v05.yml` is confined to this research branch. GitHub `workflow_dispatch` is not registered for direct execution unless a workflow exists on default branch. No future scheduler or outside runner was activated, and `main` is untouched. Hence no new Nov1+ real forecasts or market results exist yet. A separately authorized operational setup is required to execute repeated prospective observations. No assistant background operation has been promised.

### Regression evidence
- Source-only seven synthetic clock tests PASS as part of [#41096454537](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41096454537).
- Nov frozen V0.3 10 model causality/ABSTAIN tests and seven new V0.4 source tests **17/17 PASS**, [#41097036575](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41097036575); initial CI #41096886061 had a self-referential YAML string assertion, which was documented and fixed without scientific changes.
- V0.5 independent archive source custody **5/5 PASS** and exact-index expiry/ABSTAIN **8/8 PASS**, [#41097700645](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41097700645). Prior #41097576367 failed due Python syntax grouping error; documented before all market outcomes, fixed without changes to science. Combined **30/30 OFFLINE SYNTHETIC TESTS PASS**, NOT real forward accuracy.
- V0.5 end-to-end genuine GitHub artifact publication plus prospective index-expiry collection **NOT yet executed in November**; only source-only genuine public data proof exists.

### Why not a financial GO
Exact Event Futures server quote at bet acceptance, opening/settlement index parity, and market execution rules/costs are still not verified. Visible book quotes can be canceled/spoofed, not actual executed flow. Minimum frozen prospective >=300 resolved qualified non-tie observations across >=20 days, independent final chronological third and daily-block 95% lower payoff CI >0 (plus multiple testing) are not met. At q=.70, a 58.82% hit rate is **bare breakeven before costs**, not enough evidence for profitable execution.

**Operational scientific verdict: SOURCE_READY_FOR_FUTURE_PAPER_TRIAL / ECONOMIC_EDGE_UNTESTED. Capital, live, leverage and automated exchange trading = BLOCKED.** Previous Sep protected and Oct05-30 NVDA forward untouched. No new strategies initiated, accounts/orders/wallets/private exchange API/paid source/main merge.
