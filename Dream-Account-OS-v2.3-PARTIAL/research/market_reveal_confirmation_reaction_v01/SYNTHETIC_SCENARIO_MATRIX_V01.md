# MRCR V0.1 — Synthetic Scenario Matrix
Status: SYNTHETIC QA ONLY / NO SCIENTIFIC OUTCOMES

The scenarios below exist only to test implementation invariants. They are not economic thresholds, backtest cases or classification examples.

## S1 — aligned positive response

Synthetic positive decision-time price displacement and positive aggressor imbalance.

Expected invariant:
- alignment sign = +1;
- response-per-unit-flow > 0.

No claim is made about what happens after the decision timestamp.

## S2 — aligned negative response

Synthetic negative displacement and negative aggressor imbalance.

Expected invariant:
- alignment sign = +1;
- response-per-unit-flow > 0.

This verifies sign symmetry.

## S3 — flow opposed by price

Positive flow imbalance with negative price displacement, and the symmetric opposite case.

Expected invariant:
- alignment sign = -1;
- response-per-unit-flow < 0.

This is an implementation state, not a reversal forecast.

## S4 — partial retracement before decision

Impulse extreme occurs before the decision timestamp and price has moved back toward the pre-impulse anchor by decision time.

Expected invariant:
- retracement fraction follows the frozen mechanical formula;
- both positive and negative impulses are symmetric.

## S5 — zero flow

Buy and sell aggressive notional are equal.

Expected invariant:
- flow imbalance = 0;
- price-response-per-unit-flow is undefined rather than infinite or imputed.

## S6 — depth removal

Absolute depth quantity becomes zero.

Expected invariant:
- zero quantity is valid as a level removal;
- it is not treated as a negative or missing quantity.

## S7 — sequence gap

Synthetic Binance or Coinbase update identifiers skip required continuity.

Expected invariant:
- gap is detected;
- downstream state must fail closed/resynchronize rather than silently accept uncertain book state.

## S8 — out-of-order/duplicate

Current sequence is not greater than prior sequence.

Expected invariant:
- state is explicitly marked out-of-order/duplicate where source semantics require it.

## S9 — future observation contamination

An otherwise-valid observation has a timestamp later than the supplied decision timestamp.

Expected invariant:
- strict boundary guard detects/rejects it;
- the future row cannot enter the decision state.

## S10 — raw evidence hash

Identical raw bytes produce identical SHA-256 fingerprints; any byte change produces a different fingerprint.

Expected invariant:
- raw evidence is content-addressable and tamper-evident.

## Boundary

These synthetic cases may verify code only. They cannot be used to choose a market threshold, decision clock, future-return horizon, trade direction or economic rule.
