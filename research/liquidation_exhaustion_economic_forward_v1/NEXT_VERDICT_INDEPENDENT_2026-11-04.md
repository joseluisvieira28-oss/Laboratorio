# LIQUIDATION EXHAUSTION — ECONOMIC FORWARD V1: VERIFIABLE NEXT VERDICT
Date: 2026-11-04 UTC; PR #333, research-only, no orders, account access or PnL.

## Outcome-protocol authority
Economic forward rules were frozen **before these new source observations** at commit `88e7632c77c2d0fccc856d59d621caaf5f590658`. BTC only; independent 2+ same-side liquidation children within 10s with notional proxy >=100k USDT; absence and absorption/recovery triggers; paper 5s delayed entry, 60s MEXC crossed BBO exit, illustrative 20bps/base and 36bps/stress cost including adverse market impact; 15/30s delay diagnostics. Primary evidence needs >=60 independent eligible episodes across >=14 UTC dates, 90% complete paper quotes and robust confidence. Old LICP #107 NO_EDGE is NOT reopened. 2026 protected holdout not opened.

## Stage 1 — original MEXC ticker FAILED
Original real run #41872000026; artifact #13344184977 SHA256 db72f8e6f44601a4f32021958b8e69e65ea840358feecf6ede136d10249c00f1; 240 seconds, Bybit 9,366 contiguous book deltas, 5,903 trade child events, zero liquidation children observed. MEXC BTC Futures ticker 94 real bid/ask packets, 64 older than 1500ms frozen freshness max, 30 fresh. Original collector counted 18 eligible with sticky post-stale warm flag, but independent strict re-quarantine yields **1**. Original source verdict MEXC_EXECUTABLE_QUOTE_SOURCE_BLOCKED. Collector bug corrected only in later code, not retroactively in run.

## Stage 2 — alternative public MEXC depth source PASSED
Separate source freeze v1.1 at commit `f3f3ef4cba6a702657166a4d6daa14bd9a63e0af`; genuine run #41873154369, artifact #13346670234, ZIP SHA256 7dce838df2c90ace437aec8f485009aa26c53d54c6b2cc3f52d24d3ce6c83309.
- 120.242s MEXC BTC_USDT Futures public depth 5, **427 fresh snapshots and 425 accepted after 3-frame warm-up**, exchange-ts-to-local-receive lag **57–103ms**, zero stale depth or reported source errors.
- Raw stream 426 consecutive quote update gaps: median **272ms**, maximum **527ms**, 0 gaps over 1500ms.
- Control ticker same socket 46 frames, only 14 fresh and 32 stale. This is empirical improvement in publisher timestamp freshness for THIS window, not proof of financial gain or guaranteed order fills.

## Stage 3 — same-time Bybit liquidation + MEXC fresh depth PASSED (bounded)
New independent source freeze v1.2 commit `55e31a84eccd3410d6f81a7a847fc87d8aae2c8e` before new raw data.
- Real one-shot 240s run [#41873910456](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41873910456); original artifact **#13344759793** downloaded, ZIP SHA256 **ceba3e7b19ff1226d3f84c424c3fca904d8bdc9f59b969ae1a1939bfcfe4c736** (matches GitHub digest); raw NDJSON SHA256 **ddc79738929f40028a4e0702eb7f3028bb4e74a9a57edef533df30d5c6e2f96f**.
- Bybit 10,359 orderbook messages: 1 snapshot + **10,358** contiguous deltas, **7,878** real trade child records, **1** genuine observed BTC liquidation child; no transport errors, 16/16 pongs; liquidation's event->receive lag 264ms.
- MEXC full-depth **856** valid fresh messages, **854** eligible after warm-up, **zero** stale, source maximum latency 93ms, 16/16 pongs, zero transport errors.
- The *one* observed liquidation had previously received Bybit orderbook within **26ms**, last Bybit trade within **170ms**, and a pre-event MEXC full-depth BBO within **201ms**. Source causality measured by receive order, NOT future returns.
- **Independent GitHub Actions replay run [#41874863741](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41874863741)** downloaded original artifact from GitHub, checked both exact hashes, all source counts + contiguous book, and 1/1 liquidation co-timed with all three prior feeds. Logs PASS and immutable independent artifact **#13345413588** ZIP SHA256 **12ec7ab37412a4f9b72653e4604bac38f9e58722ee333d79fb1c6d347d7349e4**, source verdict `JOINT_SOURCE_WINDOW_CAUSAL_PASS_LIMITED`.

## Crucial economic distinction
**Only 1 liquidation child was seen in V1.2; the fixed economic trigger requires 2 or more of the same liquidation-position side in a 10-second window, with 100k USDT aggregate notional proxy AND further exhaustion/flow/price checks. So there are 0 eligible economic decisions in this sample.** This is NOT 1 profitable trade, not a strategy sample, and not NO_EDGE. Observed positive source event is also not proof of complete market-wide liquidation event census; large positions may not all be visible.
No trade returns, fills, 60s future outcomes, win rate, realized profit, modeled net PnL or leveraged account effects were assessed; user's actual manual MEXC fee tier/trading eligibility, size, order book depth and funding remain UNVERIFIED.
The MEXC best-bid/ask depth source is plausibly usable for **paper quote** studies, but executable fill/size/parity remain unproven. A sample of one cannot estimate reversals or return distributions.

## Binding next veredict
**SOURCE_WINDOW_CAUSAL_PASS_LIMITED / ECONOMIC_FORWARD_INSUFFICIENT / REAL_EXECUTION_ROUTE_UNVERIFIED / NO_LIVE_GO.**

This phase closes the narrow *instrument/source access* blocker. Do not burn more short independent source-only runs with no feasible economic sample. A future study must collect genuinely new, chronologically independent positive *episodes* over >=14 UTC days; keep fixed detector/cost/latency assumptions; and preserve every missed/censored episode. Evaluate outcomes only at the preregistered adjudication gate; if sources fail label SOURCE_BLOCKED, if underpowered INCONCLUSIVE, never invent profits. Any ongoing collection, scheduled check or paid API requires separate operational authorization before activation. No main merge.
