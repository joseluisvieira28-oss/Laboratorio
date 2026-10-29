# EVENT FUTURES ATI — FIRST HISTORICAL SOURCE + PROXY CLOSEOUT
Date: 2026-10-29. Research-only, no main merge, no live, no private/market orders.

## Phase A — source-only gate independently executed
- GitHub Actions [run #40864318462](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40864318462), head 83634a62bf11946c837e89d52728b2d3abd7f63f, job 123415098587, artifact 12892547807, artifact SHA256 07f055f9239536d9904dbe23240724fa8bfe7953cae73f27b806abc2c16637d3.
- PASS: official Binance Vision 2026-04-01 USD-M aggTrades, BTCUSDT **1,591,573** rows and ETHUSDT **1,548,304** rows, **1,440/1,440 active minutes per symbol**.
- Original ZIP publisher SHA256: BTC 7926f51d0d6d8cf4b83e735552920972b2b50e8a7fc593ecde4d39bd5666482e; ETH 02aad71a3c78d9d1ae28d5ed185d117cfaa33c5c053cb73dc8d59fd3d1f84a03.
- Publisher hashes match, schemas valid, strict monotonic event timestamps, raw source + derived minute flow SHA receipts.
- Source event-time is **not** source collector arrival time, historical archives can be revised and become available after the day. This is genuine historical source feasibility ONLY, not prospective as-of custody.

## Phase B — frozen descriptive one-day proxy
- Frozen rule/source/benchmark/10m+30m before this joint ATI/index evaluation. Freeze: ATI_ONE_DAY_PROXY_FREEZE_V01.md. April price outcomes were already exposed by prior index-only Discovery; therefore **not independent OOS**.
- GitHub Actions [run #40864653127](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40864653127), head db91c5ac819ecd7e3894ae465d7736b8ae1999d6, job 123416232150; artifact ID 12892358632, SHA256 5327586929178d9a878b9b962b45466752166773047b3106f4bcc55969ed2d74.
- Rule = sign of aggressor BUY minus SELL notional across 3 **completed** 1m bins; equal -> no decision. Nonoverlapping decisions per symbol/horizon; comparator ALWAYS UP on exactly the same timestamps. Index outcome from public MEXC standard-futures index Min5 OPEN(t) vs OPEN(t+H), not verified Event Futures order open/settlement.

| Symbol | H | N (incl ties) | ATI wins/losses/ties | ATI accuracy ex ties | Always UP accuracy ex ties | ATI illustrative EV at payout 80% | ATI illustrative EV at payout 85% |
|---|---:|---:|---|---:|---:|---:|---:|
| BTC | 10m | 141 | 68/73/0 | 48.23% | 51.06% | -0.13191 | -0.10780 |
| BTC | 30m | 47 | 26/21/0 | 55.32% | 51.06% | -0.00426 | +0.02340 |
| ETH | 10m | 141 | 73/68/0 | 51.77% | 50.35% | -0.06809 | -0.04220 |
| ETH | 30m | 47 | 24/22/1 | 52.17% | 58.70% | -0.05957 | -0.03404 |

- At 80% payout, **0/4** ATI cells positive theoretical EV. At 85% payout, **1/4** ATI cells positive theoretical EV (BTC 30m, 26/47), fragile and chosen AFTER viewing the four outcomes. Such a subset must NOT be promoted or treated as independent evidence.
- ETH 30m ALWAYS UP benchmark happens to be positive hypothetically in this tiny one-day sample; no strategy claim or valid economic edge either.
- 0 protected September 2026 outcome accessed, 0 real payouts observed, 0 live orders/account requests. No observed market risk-adjusted/independently verified edge.

## Decision and next scientific gate
**SOURCE_PASS / ONE_DAY_DESCRIPTIVE_ONLY / NO_INDEPENDENT_EDGE / NO_LIVE_GO.**
The source is useful, but the simplistic continuous 3m signed flow is not robustly promising in this one-day illustration. Do NOT optimize windows/directions, exclude losers, or re-open previously rejected LICP or static L2 studies to rescue it.

A separate genuinely prospective preregistration must bind public as-of feed receipt timestamps, MEXC index decision/expiry ticks, actual observed direction-dependent payouts, independent samples and multiplicity corrections before any claim of edge. Alternatively, a **new distinct economic mechanism** may be source-gated. No costs incurred, no main changes.
