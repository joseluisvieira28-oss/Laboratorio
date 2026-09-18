# CED-1D AVAX20 — V3 EXECUTION FEASIBILITY FREEZE — 2026-09-18

**Status:** FROZEN BEFORE AVAXUSDT 2025 AGGTRADES ACCESS  
**Branch:** `ced-1d-v3-byte-recovery-2026-09-17`  
**Candidate:** `CED1D-0031` only — AVAXUSDT Momentum 20D CONTINUATION H1  
**Purpose:** close the Promotion Policy V3 execution-feasibility hard gate. This does **not** rewrite the historical strict V0.2 Confirmation FAIL.

## Immutable evidence parent

2025 one-shot run: `35340971526` — SUCCESS  
Artifact ID: `10545241942`  
Artifact digest: `sha256:43984d73541085b76c9071e959de34284a8940e5968e10f04664cf56369987b5`

Only the exact 357 inference-eligible AVAX target events from that immutable ledger may be evaluated. No event may be added, deleted, shifted or selected after execution outcomes.

## Venue and source

Venue: Binance USD-M perpetual futures, AVAXUSDT.

Execution evidence source:
`https://data.binance.vision/data/futures/um/monthly/aggTrades/AVAXUSDT/AVAXUSDT-aggTrades-2025-{MM}.zip`

Every 2025 monthly archive must pass provider `.CHECKSUM`, ZIP CRC, schema, strict time ordering and month bounds.

Binance public-data authority documents USD-M aggTrades as the archive equivalent of `/fapi/v1/aggTrades`, with fields:
aggregate trade id, price, quantity, first trade id, last trade id, timestamp, wasBuyerMaker.

No 2026 archive may be opened.

## Execution proxy — frozen before source access

Reference execution time remains the frozen 00:01:00 UTC entry/exit timestamp.

Desired side:
- long entry / short exit = BUY;
- short entry / long exit = SELL.

Observed taker-print side:
- BUY requires `wasBuyerMaker == false`;
- SELL requires `wasBuyerMaker == true`.

For each leg, starting at the exact reference timestamp, consume only chronological same-side observed taker prints until either:
1. cumulative quote notional reaches **100 USDT**, or
2. **5,000 ms** have elapsed.

The final print is clipped pro-rata to exactly 100 USDT. The resulting quantity-weighted VWAP is the execution proxy.

No print before the reference timestamp is allowed. No opposite-side print, midpoint, interpolation, nearest-neighbour, kline open/close or favorable substitution is allowed.

If 100 USDT cannot be accumulated inside 5 seconds, the leg is `MISSED_EXECUTION_PROXY`.

This is an auditable small-notional taker-print proxy, not a claim of full order-book replay or production capacity.

## Fees

Maker assumptions are forbidden.

BASE research fee floor:
- 4 bps per taker fill;
- 8 bps round-trip;
- no VIP/Taker Program/BNB discount.

STRESS research fee floor:
- 5 bps per taker fill;
- 10 bps round-trip;
- no discounts.

The BASE 4 bps/fill anchor is supported by Binance's published regular USD-M taker schedule in its VIP program authority; 2025 Binance Taker Program announcements describe discounts from standard VIP fees, not an increased fee assumption.

Fail-closed rule: if authoritative date-effective evidence later shows a regular AVAXUSDT taker fee above 5 bps/fill for any tested interval, the execution PASS is invalid until re-adjudicated with the higher fee. Fees may never be lowered to rescue a result.

## Executed-return calculation

For each complete execution pair:
- use the execution-proxy entry VWAP and exit VWAP;
- preserve the immutable trade direction;
- calculate signed gross execution return;
- add the already frozen **conservative funding LOWER bound** from the one-shot ledger;
- subtract BASE fees (8 bps RT) for BASE executable net;
- subtract STRESS fees (10 bps RT) for STRESS executable net.

Because execution prices themselves contain spread/short-latency effects, no separate spread/slippage amount is subtracted again.

Reference-vs-execution drag is reported separately:
`drag_bps = reference_gross_bps - execution_proxy_gross_bps`.

## Capacity / fill / latency gates

Intended V3 research capacity = exactly **100 USDT notional per leg**.

Execution feasibility PASS requires all:
- at least 99% of the 714 required legs produce a 100-USDT proxy within 5 seconds;
- at least 99% of the 357 events have both entry and exit proxies;
- median leg latency <= 1,000 ms;
- p95 leg latency <= 5,000 ms;
- mean total nonfunding cost proxy (8 bps BASE fee + observed execution drag) <= 14 bps round-trip;
- p95 total nonfunding cost proxy <= 20 bps round-trip;
- BASE executable funded mean > 0;
- BASE executable funded PF > 1;
- STRESS executable funded mean >= 0;
- no single month >30% of absolute executable PnL;
- no top-5 events >20% of absolute executable PnL;
- no single day >10% of absolute executable PnL.

Negative execution drag is retained; no clipping to zero.

A miss is never silently dropped from the fill-rate denominator. Economics are reported on complete pairs and the miss rate is an independent hard gate.

## V3 adjudication

If every execution-feasibility gate passes, CED1D-0031 may be re-adjudicated under the already-frozen Promotion Policy V3 Standard Replication Path using:
- positive independent 2025 OOS BASE economics;
- PF >1;
- N=357;
- 7/12 positive months;
- non-catastrophic concentration;
- execution feasibility at the frozen 100-USDT research notional.

That permits **Tier 2 — Promoted Candidate / Quase Diamante** only. It does not authorize live trading, capital, production, alerts or orders.

If execution economics are negative/PF<=1 or fill feasibility fails, the candidate remains Tier 3 or is rejected only if the evidence materially contradicts execution feasibility.

## Prohibitions

No 2026+. No signal change. No lookback/horizon/direction change. No event deletion. No fee reduction. No maker rescue. No order-book assumptions. No live trading. No exchange mutation. No orders. No wallets. No alerts/webhooks. No merge to main.
