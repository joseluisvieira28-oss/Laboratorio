# EVENT10M CROSSVENUE PRICE SOURCE — FINAL OPERATIONAL AND SCIENTIFIC VERDICT (2026-10-30)

**SOURCE REPAIR: PASS, BUT ZERO CERTIFIED PREDICTIVE OR ECONOMIC EDGE.**

## Economic objective and scientific scope
Determine whether Binance USD-M public BTC/ETH aggregated-trade price receipts and MEXC public underlying INDEX price receipts can provide reliable as-of observability, then only in a separate preregistered study evaluate whether any event-conditioned predictive probability of a **future** 10-minute direction exceeds decision-time Event Futures payout break-even and human delivery/execution costs. **This closeout covers source-engineering only.**

NVIDIA explicitly excluded (separate project/chat). Do not resurrect 3-minute signed-flow PR #277 historical NO_EDGE, retired LICP PR #107, static arbitrage PR #289 NO_ARB, or reinterpret historical proxy payouts. No protected September 2026 holdout accessed. All tasks were public/read-only, no trades, user accounts, API keys, MEXC Event Futures private order routes or Telegram delivery.

## Trial A — Original V0.2 price source, fixed 180s window
PR #294, run [#41032128118](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41032128118), job 123984098829, source artifact ID **12965304781**, sha256 **06049331f8e52aaca4f48b88ab8855b243d54e5e5cc8e3e10e3bfee03b45126e**. **PRICE_SOURCE_INCOMPLETE**, 179.65s overlapping socket origin:
- Binance valid BTC 2111/ETH 1671 market aggr.trade messages.
- MEXC valid BTC 59/ETH 55 public INDEX messages; last MEXC index values observed at 63.795s BTC / 63.625s ETH from first joint observation, while Binance continued all 180s.
- V0.2 as-of paired local monotonic price grids, fixed 5s grid / 15s trailing source returns / price age <=5s: **BTC 9, ETH 11 valid pairs** against >=18 gate per asset. Frozen source FAIL; do not lower threshold.
- Contemporaneous correlation BTC 0.9482 / ETH 0.9430 computed on 9 and 11 OVERLAPPING descriptive samples, not statistically reliable and not forward predictions.
- MEXC transport got `ConnectionClosedOK:received 1005` with no application-level ping in this code.

Independent offline artifact-forensic [#41032793387](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41032793387), job 123986309784, artifact ID **12966398671** sha256 **b225ebb10759d9fb1cb5f362ac57e4cc39ee5cbc70f8786406ef2e024e0e9c9b**, read only the existing archived receipt, did not request market prices. Verified gap BTC 115.926s and ETH 116.096s from last MEXC valid tick to end; zero MEXC ticks in LAST 60s while Binance continued. Source audit thus identified a real streaming continuity defect, not a price lead.

## Trial B — V0.3 attempted re-subscription (failed)
PR #296, run [#41033008818](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41033008818). Separate freeze: same 180s, same prices, same science/gates, only repeated public sub.index.price subscriptions every 40 seconds. The connection ceased after one renewal and did NOT meet source criteria: BTC 12, ETH 12 valid paired as-of bins vs fixed >=18; MEXC closed with the same ConnectionClosedOK. Do not relabel this failure a PASS.

## Trial C — V0.4 DOC-SPECIFIED JSON APPLICATION HEARTBEAT (PASS)
Official MEXC Futures WebSocket documentation https://mexcdevelop.github.io/apidocs/contract_v1_en/ specifies an **application payload** `{"method":"ping"}` and a server `{"channel":"pong"}` response. It explicitly says no ping within 1 minute disconnects the connection and recommends 10-20sec ping interval. This is distinct from RFC6455 automatic control-frame pings of the Python websockets library, used in V0.2. Our page-supported wss://futures.mexc.com/edge exhibited compatible behavior, confirmed empirically by this separate test; do not assume all MEXC hosts identical.

V0.4 was frozen **before** its source observations, isolated PR [#297](https://github.com/joseluisvieira28-oss/Laboratorio/pull/297). It changed ONLY the MEXC public application-level `{"method":"ping"}` every exactly 15s, no repeated subscription and no other scientific threshold/price source logic.

Authoritative [SUCCESSFUL run #41033215522](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41033215522), job 123987685520, artifact **12966014308**, original source archive sha256 **e7f7b2c9cdf9edb5238c4df5850535d4d8c52984c79d945ead4eda0d4466ab38**.
- Source sockets overlap 179.64s and both remained healthy, **no error**.
- **11 public JSON application pings sent / 11 server pongs acknowledged.**
- BTC valid Binance aggTrades 2169; MEXC public index updates 141; **32** as-of 15s trailing grid price-return comparisons; 32 nonzero both; contemporary sign agreement **29/32**, Pearson **0.9482236672**.
- ETH valid Binance aggTrades 1520; MEXC public index updates 140; **34** paired as-of grids; 31 nonzero both; contemporary sign agreement **28/31**, Pearson **0.9585631885**.
- Frozen minimum >=18 valid price grid pairs per symbol and >=10 per venue nonzero-return pairs, >=120s overlap and no transport errors PASS.
- Fixed 5bp previous-15sec Binance movement tag: 3 BTC, 4 ETH *contemporaneous* comparisons; both same-time MEXC signs matched 3/3 and 4/4, respectively; these are overlapping and not independent, never 10m future outcomes or trades.
- Any index+trade comparison remains **different underlying price reference** (Binance perpetual traded price vs MEXC composite/reference index); similar historical movement in prior 15s is not a causal information advantage, opportunity or execution price.

## Three scientific gates and decision
1. **Price SOURCE availability and as-of comparability**: PASS in ONE 180s forward test with documented application JSON ping. Earlier two source-only receipt tests in PR #291 also passed 45s each, but did not test multi-minute liveness. A single 180s PASS does not establish weeks-long 24/7 feed reliability; production needs heartbeat, reconnect/backoff and source health watchdog. Keep frozen CI on isolated research branch; DO NOT merge to main or deploy.
2. **Event-conditioned NEXT TEN MINUTES directional probability and payout-adjusted advantage**: NOT TESTED. Zero 10m forecasts, zero resolved 10m outcomes, no pre-outcome calibrated independent p(UP) model, no exact decision-time observed payouts joined to those market events, no actual Event Futures server-set order entry/settlement parity. PR #275 predefines minimum 30 calendar days, >=150 independent resolved non-tie cases per cell and matched baselines, calibration, Holm/time-block uncertainty before any promotion. The old PR #289 public payouts (BTC q=0.70; ETH q=0.80 at Oct29 instants) imply illustrative break-even rates 58.82%/55.56% *AT THAT TIME*, not probabilities or current payoff guarantees. Zero real Event Futures outcome receipts collected here.
3. **Telegram human delivery and executable Event Futures timing**: NOT TESTED / BLOCKED. No Telegram message sent, delivery/read receipts, user-action timestamp, actual server-assigned entryPrice or funds movement. Official Event Futures support https://www.mexc.com/support/futures-trading/event-futures says Event Futures API trading not supported (Futures standard API distinct product). No live GO.

**FINAL VERDICT**:
- Operational defect: **MEXC PUBLIC INDEX FEED HEARTBEAT MISSING — RECOVERED IN BOUNDED V0.4 RUN**.
- Source gate: **PRICE_COMPARABILITY_SOURCE_PASS** only for observed ~3-minute test.
- Price lead: **NOT ESTABLISHED**.
- Economic edge and profitability: **NO EDGE CERTIFIED / ZERO 10m RESULTS**.
- Next legitimate work: separate new prospective preregistered **same-event price-response** and actual Event Futures payout/settlement shadow collector with strict as-of UTC+monotonic receipt and frozen model; accumulate independently resolved full batch, do not adapt after outcomes; optionally human-operated Telegram dry-run without financial execution if user deliberately chooses to validate delivery. No repeating the old failed 3m flow or pretending that a transport PASS is a trading GO.

No protected holdout, NVIDIA, accounts, orders, wallets, private exchange API, paid sources, fees, auto-scheduling, deploy, merge or main changes.
