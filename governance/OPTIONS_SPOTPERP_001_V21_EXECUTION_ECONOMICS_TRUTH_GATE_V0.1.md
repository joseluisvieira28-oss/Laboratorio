# OPTIONS-SPOTPERP-001-V2.1 — EXECUTION ECONOMICS TRUTH GATE V0.1

**Date:** 2026-09-28  
**Status:** FROZEN EVIDENCE / EXECUTION-ECONOMICS AUDIT LAYER  
**Parent execution fork:** OPTIONS-SPOTPERP-001-V2.1-FUTURES-ONLY-AUTOLIVE-V0.2.1  
**Science changed:** NO  
**Trading rule changed:** NO  
**Main merge:** NOT AUTHORIZED

## Question

Determine whether the frozen V2.1 signal has economically executable headroom on the current MEXC BTC_USDT Futures API route after actual fees, fills, funding and observable slippage, without retuning the scientific hypothesis.

## Frozen historical reference

2025 independent OOS:
- NET10 mean = +5.0427663334 bps/opportunity.
- NET20 mean = -4.6759378383 bps/opportunity.
- 363 entered scaled trades.
- Cost model is linear in executed weight.

The two frozen cost points imply an average executed weight of 0.97187041717 and an implied gross mean of 14.7614705051 bps/opportunity. Under the same historical population, a 16 bps full-notional execution cost implies approximately -0.7884561696 bps/opportunity. This is a sensitivity bridge only; it does not rewrite the OOS result.

## Current MEXC API fee authority

MEXC's 2026-05-28 announcement, effective 2026-06-01, states Futures API maker 0.06% and taker 0.08%. API fees supersede web/app promotions. The current Futures-only executor uses MARKET orders, therefore the conservative official taker floor is 8 bps/fill, 16 bps for two fills before spread, slippage and funding.

The previous executor constant 5 bps/fill was stale. V0.1 hardens the execution gate to 8 bps/fill; this is a safety/economic correction, not a scientific parameter change.

## Evidence chain required per trade

A trade receives a complete economic verdict only when one immutable identity links:
CANONICAL_EXECUTION_SIGNAL -> ORDER_INTENT -> PRE_ORDER_GATE -> FILL_RECEIPT -> ACTIVE_TRADE_STATE -> EXIT_INTENT -> PRE_EXIT_MARKET_SNAPSHOT -> EXIT_FILL_RECEIPT -> POST_TRADE_RECONCILIATION.

Missing or mismatched evidence => EVIDENCE_INCOMPLETE / no economic verdict.

## Metrics

For each completed trade:
- actual entry and exit order IDs / external OIDs;
- entry and exit notional;
- fee on each fill and round-trip fee bps;
- entry slippage vs pre-order touch;
- exit slippage vs pre-exit touch when snapshot is available;
- signed funding effect;
- gross close PnL;
- realized net PnL and bps.

Slippage is diagnostic and is not added a second time to realized PnL because actual fill prices already embody price execution.

## Buckets

- <=10 bps round-trip fee: fee-only compatible with BASE10 before other friction.
- >10 and <=20 bps: between BASE10 and STRESS20.
- >20 bps: above STRESS20 before other friction.

No bucket is a promotion or trading recommendation.

## Current evidence from operator export

Five recent BTCUSDT MARKET fills at 1x each show about 8.40-8.44 USDT notional and 0.0067 USDT fee per fill, equivalent to roughly 7.94-7.97 bps/fill and ~15.9 bps two-fill fee equivalent. The export does not contain signal IDs or external OIDs, so these rows cannot be attributed to V2.1 without local executor receipts.

## Immediate verdict

The current MEXC MARKET/API route is **not BASE10-compatible on fees alone** under the official 8 bps/fill schedule. It sits around 16 bps round trip before spread/slippage/funding. The historical OOS sensitivity bridge is slightly negative at 16 bps. Therefore the next legitimate question is not whether fees are "small in cents"; it is whether the exact realized V2.1 trades produce enough gross edge to overcome roughly 16+ bps total friction.

No new discretionary/test order is authorized by this audit. Existing canonical auto-microlive authority remains governed by its own gates.
