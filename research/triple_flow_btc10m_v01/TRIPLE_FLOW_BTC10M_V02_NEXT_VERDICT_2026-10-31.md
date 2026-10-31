# TRIPLE FLOW BTC10m — NEXT LEGITIMATE SOURCE GATE VERDICT
Date **2026-10-31**. BTC only. Two strictly preregistered live public-source experiments. **ZERO forecasts, ZERO 10-minute outcome labels, ZERO trades, ZERO capital, main unchanged.**

## Final exact scientific classification today
- **V0.1 FROZEN JOINT REST+WS GATE: SOURCE_BLOCKED.** Independent forensic integrity PASS, source eligibility FAIL.
- **V0.2 FROZEN 3-VENUE PUBLIC WS GATE: SOURCE_BLOCKED (one startup MEXC index frame stale), but substantial confirmed fresh market trades exist on all three venues.** Do not replace frozen FAIL with semantic PASS.
- **EXECUTED_TRADE_FEED_FEASIBILITY: REAL POSITIVE, limited to this 120second capture; raw semantics independently verified.**
- **LIQUIDATION_POSITIVE_EVENT_GATE: NOT MET**: 0 Bybit BTC liquidation events in BOTH new live probes; no proof that no liquidations occurred at exchange, no liquidation side/notional calibration from this new data.
- **FULL_60S_ROLLING_TAPE_COMPLETENESS: NOT CERTIFIED**: no packet-loss/exchange-sequence proof; REST 100cap snapshots DO NOT provide a trade census.
- **ECONOMIC_10M_DIRECTIONAL_EDGE: UNTESTED.** WIN RATE N=0, EV N=0; payout per prospective decision, official Event Futures entry & expiry exact quote parity unresolved.
- **TRADING_REAL/MEXC EVENT FUTURES LIVE: NO-GO**.

## V0.1 original 150sec freeze & completed original read-only run
Freeze commit `7a0a16676726858b37259cdada4f9c9de78ecd4f`, original code execution HEAD `489e7a6d6ae223ea1a668729b60cc68b5a93c5cd`.
[Run 41232706472](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41232706472), uploaded original artifact **13054576473**, server ZIP SHA256 **94dfe1e421a8b27836bdd367d303bd261b056df5eefac79bf66fc9520322201c**.
- 10/10 offline parser tests PASS; raw Bybit BTC 100 signed trade child events (82 BUY, 18 SELL) in 64 frames, no transport error, zero liquidation event frames in 150sec.
- 30/30 MEXC standard Futures deal REST responses valid but **max 100 most recent only** and not complete executed flow; OKX spot GET 20/30 valid at <=5sec, 10 stale; MEXC public INDEX REST 15/30 valid at <=2sec and 15 stale; MEXC DEPTH 0/30 due exact parser error `MEXC_PRICE_OR_BOOK_SYMBOL`: public depth data omits `symbol` though HTTP URL carries it. This failure is technical and must be preserved, not called source pass.
- Bybit sent nine application pings, the original code reported zero pongs. This was a **real parser error**: raw frames show nine `{"op":"ping","ret_msg":"pong"}` responses. No server heartbeat failure could be established.
- [Independent original SHA/side/count replay #41232994886](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41232994886) PASS: exact raw 3-member archive, 100 Bybit trade events, 30 MEXC valid deal responses, 15 index, 20 OKX trade, zero accepted MEXC depth; explicit REST errors and real pong semantics externally reconstructed.
- No outcome labels; no simulated sign of predictive power.

## V0.2 pre-frozen 120sec 3-WebSocket replacement
V0.2 freeze commit `9fe40a48514137678764c9480898a4436186257a`, source execution HEAD `7da1c1dcf2865deb2b0c5dd99b01364c0a327393`.
[Run 41233170304](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41233170304) original artifact **13054746594**, server ZIP SHA256 **4cb8a1da92259554271231f7e610548044d8d76d73a62d1c172282531e5ca876**.
- **8/8 offline tests PASS**, including Bybit `op=ping,ret_msg=pong` correction, source timestamps, trade and liquidation side, no false source promotion.
- All THREE public WebSocket transports connected simultaneously for 120seconds, every venue reported `completed_window=true`:
  - **Bybit BTCUSDT linear:** 453 actual signed BTC trade child events (337 BUY, 116 SELL), 84 trade frames, 8/8 ping/pongs, clean schema, max trade event receive age **199ms**, ZERO observed liquidation frames/children; no claim Bybit or market had zero liquidations.
  - **OKX BTC-USDT Spot:** 113 signed trade events (83 BUY, 30 SELL), 113 trade frames, valid public subscription, 7 pongs, **0 schema/clock errors**, peak trade receive latency **78ms**. WS port 443 avoids Oct31 port 8443 retirement.
  - **MEXC BTC_USDT regular perpetuals:** 268 valid signed trade events (155 BUY, 113 SELL), 228 trade frames; 20 accepted public futures index push messages; valid public subscription; max validated event receive age **299ms**; **one source-only stale startup index frame**.
- **Exactly 834 validated signed trade child events** across the 3 sources (453+113+268), not unique across exchanges. These are independent BTC venue prints, NOT 834 predictions or liquidation signals.
- **Frozen V0.2 required EVERY observed frame <=2sec old and no schema errors**, therefore source correctly FAILS CLOSED. It is scientific misconduct to call this green because 20 fresh index messages happened after one bad startup snapshot.
- [Independent exact original artifact replay #41233391235](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41233391235): downloaded original SHA-pinned artifact, replayed exact raw WebSocket frames, matched trade sides/counts, timestamps, original fail; synthetic tamper checks 2/2 PASS. **Only failure**: MEXC channel `push.index.price`, raw source `ts=1793473972888` delivered at `received_ms=1793474000867`, age **27,979ms**. This is an initial **stale index message**, not an authenticated fill/open/settlement quote. All other MEXC valid frames parsed and passed age validation. Original source gate still SOURCE_BLOCKED.
- Cross-venue execution counters are preliminary schema evidence and cannot establish complete 60s flow windows, complete liquidations or incremental prediction accuracy; market prices after the decision not opened.

## Concrete next scientific decision
**NEXT GO is only to a *new* preregistered source-only experiment that documents subscription-startup stale snapshot quarantine while forbidding its inclusion in prediction features, then establishes window coverage/clock sync and observes actual liquidation event payloads over a materially longer window.** This would be a separate V0.3 source gate, not a retroactive rescue of frozen V0.2. Require exchange sequence/packet continuity and contractSize multiplier before USD signed notional. An alternative executed-flow-only hypothesis can be created as a DISTINCT new research family, but cannot be called TRIPLE FLOW and cannot reuse evaluated data as holdout.

Do not develop a 10min model from today's totals alone. Once source quality passes, a new pre-outcome freeze for UP/DOWN/ABSTAIN requires dynamic exact BTC Event Futures payout, definitive Event Futures contract open/expiry index semantics, independent preexpiry custody, first future 10min index tick and >=300 qualified independently resolved non-tie decisions on >=20 days with untouched independent holdout, baseline beat and daily-block confidence lower bound on net EV>0 after costs and latency. BTC q=.70 observed on October 30 source-only => break-even 58.8235% (not a current assumption for future event decisions). Old BTC V0.3 depth-divergence experimental Nov forward and protected Sept/Nvidia holds unchanged.

**VERDICT TODAY: WE HAVE REAL THREE-VENUE PUBLIC EXECUTED BTC TRADE DATA AND ONE UNCOVERED STARTUP INDEX FRESHNESS DEFECT, NOT AN ECONOMIC DIAMOND.** No live trading, account API, funds, secrets, wallets, paid source, scheduled collector, or main changes.
