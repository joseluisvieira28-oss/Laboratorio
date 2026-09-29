# BTC-CONVEX-TREND-CAPTURE-001 — CHILD HYPOTHESIS FREEZE — STICKY TRAIL H1

**Frozen:** 2026-09-23 before any untouched cross-asset or prospective outcome is opened  
**Parent:** recovered Quant Trailing v5 (Payoff Invertido)  
**Status:** NEW CHILD HYPOTHESIS / ZERO BTC-SEED PROMOTION CREDIT

## Motivation

Source audit found that the parent V5's “Ativa trailing após lucro %” is not actually latched.

The parent recomputes:

`stopFinal = lucroAtual >= 5% ? max(trail, initial_stop) : initial_stop`

on every execution.

Therefore a trade can enter the trailing regime and later revert to the original -4% stop when close-based profit falls below +5%.

This source-semantic observation motivates, but does not validate, a child hypothesis.

## H1 change

Change **one semantic property only**:

> Once a confirmed-bar close first reaches >= +5% profit, trailing mode becomes permanently active until the position exits.

All other parent parameters remain frozen:
- exact parent entry signal;
- long-only;
- SMA200 regime;
- initial stop = 4%;
- trailing distance = 12%;
- activation level = +5%;
- 95% equity sizing for reproduction views;
- 0.10% commission each side for parent-comparable diagnostics.

## Intended causal implementation

- entry signal only on confirmed bars;
- market entry next bar open;
- initial 4% protective stop active immediately after fill;
- no same-bar historical reentry based on final current-bar information;
- peak uses only prices observed after entry;
- once a completed-bar close first reaches +5%, `trailActive=true`;
- `trailActive` remains true until exit;
- active trailing stop = max(initial stop, peak × 0.88).

## Contamination boundary

BTC 2019-2026 parent outcomes have already been inspected.

Therefore:
- this child may be illustrated descriptively on BTC;
- BTC 2019-2026 cannot count as independent validation;
- no parameter may be changed because of BTC child results.

## First valid scientific evidence

Only evidence declared before opening outcomes can validate H1:
- mechanically identical cross-asset application with no retuning; and/or
- prospective forward observations after this freeze.

Any cross-asset universe, cost model and evaluation horizon must be frozen before its outcomes are opened.

## No rescue rule

If H1 fails untouched evidence:
- do not change +5%;
- do not change 12%;
- do not alter the parent entry rule;
- do not select a winning asset/timeframe post hoc.

A different change requires a new child ID and new pre-outcome freeze.

## Promotion boundary

H1 has **zero current promotion credit**.

No live trading, exchange mutation or main merge is authorized.
