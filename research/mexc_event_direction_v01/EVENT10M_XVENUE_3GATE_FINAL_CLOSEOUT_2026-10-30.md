# EVENT-10M BTC/ETH CROSS-VENUE — FINAL V0.1 SCIENTIFIC CLOSEOUT
Date 2026-10-30. Independent research family E10M-XVENUE-RECEIPT-001.

## Operator question
1. Do Binance Futures aggressive executions arrive before MEXC Event Futures public index updates?
2. Does any associated event-conditioned directional probability exceed the actual 10-minute Event Futures payout break-even?
3. Can a human receive a Telegram alert and reliably enter the same effective contract quote before the putative advantage vanishes?

## Frozen scientific boundary and duplication firewall
The pre-source freeze was committed at head `5da3aa74890c17855606522d6e4e04deb4c46216`, before first stream measurements. It fixes BTC/ETH Binance USD-M public `aggTrade` combined websocket versus MEXC Event Futures `push.index.price`, 45s per run, UTC receive timestamp plus same-run monotonic receive ns, minimum 20 Binance and 2 MEXC records per symbol and 20s dual-socket overlap. No prices, returns, market directions, trade signals, historical settlement or target outcomes were calculated. This is not the earlier failed 3m-aggregate signed-flow predictor (PR #277), the retired LICP (PR #107), static dual-side arbitrage (PR #289), or unactivated PR #275 model. NVIDIA is outside scope.

A second run committed *only* a workflow step display-name change to rerun **byte-identical Python source**, with unchanged parameters, after recording first source-only observations. No post-outcome tuning or outcome opening occurred. No account, order, Telegram send, real trade, protected September 2026 or main merge.

## Proof of source capture (two GitHub CI runs)
[Run 1 #41013418740](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41013418740), job 123924198301, evidence artifact ID 12958358692, zipped artifact SHA256 `f25c4579597f5e89b2803ad48a6caaf30fc4c0b9e53aa0b8032c00011eb532fd`. `SOURCE_FEASIBLE_NO_EDGE`, 44.59s dual-venue socket overlap.
- BTC Binance valid aggregated execution records 246, MEXC public index updates 13; at MEXC receipt, prior Binance local receive median age **217.472515ms** (n=12, p95 438.326655ms).
- ETH Binance 223, MEXC 32; prior Binance local receive median age **120.420110ms** (n=31, p95 511.712581ms).
- Binance exchange-event `E` to runner-UTC receive offsets median 73ms for both symbols, and MEXC server `ts` to runner-UTC receive offsets median 71ms for both. **These are not validated one-way network latencies or proof of cross-exchange clock alignment.** They include unknown source timestamp-generation and clock offset.

[Run 2 #41013654002](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41013654002), job 123924940234, evidence artifact ID 12958875374, zipped artifact SHA256 `62a17830e43c560373da4b090cbcaf4b1320b3604772392f24f7753ab513ca94`. `SOURCE_FEASIBLE_NO_EDGE`, 44.54s overlap.
- BTC Binance valid aggregated execution records 324, MEXC index updates 24; prior Binance receive median age **119.417007ms** (n=23, p95 543.42142ms).
- ETH Binance 369, MEXC index 36; prior Binance receive median age **149.033467ms** (n=35, p95 596.145288ms).
- Both runs passed frozen source minima, no invalid JSON, no attempted private or trading operations.
- Event source and public index have different update rules and underlying venue; index messages need not be emitted when prices do not move. The age of an earlier trade message does not constitute a *same-event lead* or exploitable **price** discrepancy. Every recorded age is retrospective and says nothing about next 10-minute index direction. No exchange clock synchronization independently certified, GitHub job is not equivalent to notarized time custody.

## Final gate A: information-before-index
**SOURCE_RECEIPT_OBSERVABILITY_PASS / CAUSAL_PRICE_LEAD_NOT_ESTABLISHED.**
We can timestamp both sources on one runner. Cannot say Binance price information was available before MEXC had economically equivalent information; neither executable prices nor benchmarked same event were tested.

## Final gate B: conditioned probability and fair payout
**NO_PREDICTIVE_MODEL / FORECAST_COUNT_ZERO / RESOLVED_10MIN_OUTCOMES_ZERO / PAYOUT_MATCHED_OUTCOMES_ZERO / ECONOMIC_EDGE_UNTESTED.**
The 29 Oct public Event Futures snapshot (PR #289 run #40930880041) showed BTC 10m qUp=qDown=0.70 and ETH 10m qUp=qDown=0.80 at TWO points in time, *not necessarily at the new stream decisions*. One-sided probability break-even is 1/(1+q): BTC 58.823529%, ETH 55.555556%, BEFORE other costs. Dynamic payout at decision and independently calibrated, predictive p are not observed here. A payout threshold is NOT an estimate of success probability.
Prior Event Futures PR #275 explicitly requires new frozen model/feature/source authority, fresh payout and independent prospective sample. It sets 30-calendar-day forward batch and >=150 independent resolved non-tie events per tested cell, matched baselines, multiplicity correction and calibration checks. Even 150 without proven causal/model authority cannot support edge.

For scale only, under unrealistically favorable IID fixed payout and a one-sided exact binomial test with familywise 0.05 Bonferroni-adjusted for two symbols (alpha=0.025 each), n=150 would need at least BTC 101/150=67.33% wins or ETH 96/150=64.00% wins for significance against the payoff break-even H0. This is a POWER illustration, not a new activation threshold, does not adjust additional model/horizon/market snooping or dependent observations, and does not replace the full PR #275 gates.

## Final gate C: Telegram/human execution
**BLOCKED_NO_REAL_HUMAN_EXECUTION_LATENCY_RECEIPTS**.
No Telegram token, message-send acknowledgement, delivery/read acknowledgement, phone push arrival time, user touch time, UI order acknowledgment, effective Event Futures openPrice or settlement receipt was available/tested. A GitHub timestamp for a source tick does not establish human/venue latency. Official MEXC Event Futures FAQ states currently no API trading; do not automatically place orders or bypass account/UI access. Human-supervised *signal* may be engineered only AFTER proving a positive source/execution budget and independently established economics. No trading or message send performed.

## Verdict and strict next valid experiment
- ENGINEERING RECEIPTS: source gate PASS twice.
- PRICE LEAD: NOT PROVEN.
- EVENT-CONDITIONED PROBABILITY: NOT TESTED, 0 forecasts and outcomes.
- OPERATOR DELIVERY/EXECUTION: NOT PROVEN.
- CERTIFIED ECONOMIC EDGE: **NONE**.
- AUTO EVENT FUTURES TRADING GO: **NO GO**.

Preserve this as a **source capability** (one useful component), not a strategy. Do NOT re-run the historical ATI cells for better payout, reactivate LICP, simulate human milliseconds, or infer execution feasibility from unauthenticated public market streams. The next justified research is a separately frozen forward-only same-event **price-response** and payout observation collector, with an independently validated price event mapping, strict as-of timestamps, a full-batch holdout and (before any directional market outcome) model/feature hash and baselines. Human Telegram/venue effective-entry receipt data must be obtained via separate voluntary user-controlled dry-run; nothing here authorizes real orders.

### Source references
Official Binance USD-M aggTrade stream schema: https://developers.binance.info/docs/derivatives/usds-margined-futures/websocket-market-streams/All-Market-Mini-Tickers-Stream
MEXC Event Futures FAQ (no API trading): https://www.mexc.com/support/futures-trading/event-futures
Existing MEXC public index shadow stream documentation: research/mexc_event_futures/V0121_CLOSEOUT_PUBLIC_INDEX_STREAM_PASS.md
Internal payouts and math: PR #289; directional admission PR #275.

No protected September data, other repo branches merged, API keys, wallets, account reads, spending, exchange orders, trading, production deployment, scheduling or main changes.
