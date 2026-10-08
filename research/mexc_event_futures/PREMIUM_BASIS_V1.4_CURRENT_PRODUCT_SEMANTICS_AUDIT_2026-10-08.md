# PREMIUM BASIS V1.4 — CURRENT PRODUCT SEMANTICS AUDIT 2026-10-08

Status: STATISTICAL_SURVIVOR / PRODUCT_AUTOMATION_BLOCKED / SETTLEMENT_DETAIL_PARTIAL

## Scientific lineage already established

V1.2 final September holdout:
- 5/5 frozen MUUSDT FOLLOW_PREMIUM cells survived Holm-Bonferroni;
- primary prospective cell later frozen as MUUSDT / 10m / |z| >= 1.0 / FOLLOW_PREMIUM.

V1.3 integrity audit:
- INTEGRITY_PASS_ROBUSTNESS_REPORTED;
- exact September reproduction PASS;
- no feature-forward violations;
- no outcome-timestamp violations;
- no same-cell overlap violations.

V1.4 first prospective batch:
- FORWARD_EVIDENCE_ACCUMULATING;
- PRIMARY resolved included: 4;
- PRIMARY directional accuracy: 2 wins / 1 loss / 1 tie = 66.67% on non-ties;
- readiness gate not reached.

## Current official product semantics checked 2026-10-08

Official MEXC Event Futures Help Center:
https://www.mexc.com/support/futures-trading/event-futures

Confirmed:
- payout applicable to a trade is determined at submission and remains fixed for that trade;
- correct prediction returns principal + principal*payout;
- incorrect prediction loses the principal;
- a draw returns principal with no profit/loss;
- settlement value is based on the underlying price index when the Event Future expires;
- Event Futures currently do NOT support API trading;
- minimum Event Futures stake is 1 USDT.

## What this resolves

Resolved:
- payout is economically fixed at submission, not retroactively changed;
- loss is bounded by principal;
- generic settlement reference is the underlying price index at expiry;
- automated API execution is currently unavailable.

Still unresolved for exact micro-live scientific equivalence:
- exact settlement tick/sample used for MUUSDT;
- any rounding precision applied at expiry;
- proof that the public standard-futures index snapshot used by the research model equals the exact Event Futures settlement observation in every event;
- contemporaneous payout-at-entry capture for each prospective signal.

## Current classification

`STATISTICAL_SURVIVOR__FORWARD_ACCUMULATING__EVENT_FUTURES_API_BLOCKED`

This is stronger than a backtest-only candidate and weaker than an executable automated diamond.

No live trading authority.
No account/auth/private endpoint.
No order.
No wallet/capital.
No main merge.
