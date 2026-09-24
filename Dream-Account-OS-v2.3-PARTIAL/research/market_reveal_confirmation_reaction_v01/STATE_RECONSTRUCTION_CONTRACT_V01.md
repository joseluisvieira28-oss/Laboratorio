# MRCR V0.1 — Offline State Reconstruction Contract
Status: PRE-TARGET / IMPLEMENTATION-ONLY
Date: 2026-09-24

## Purpose

Build the deterministic state machine that converts canonical trade/book observations into decision-time measurements without selecting any profitable state.

## Order-book invariants

- venue-native symbol only;
- absolute quantities, never inferred deltas;
- zero quantity removes a price level;
- sequence gaps fail closed;
- stale/duplicate updates are ignored explicitly;
- crossed or locked books fail closed;
- invalid updates are atomic: a rejected batch cannot corrupt the previous valid state;
- no venue price merging;
- no USD/USDT synthetic conversion.

## BBO and spread

The engine deterministically exposes:

- best bid;
- best ask;
- mid = (best bid + best ask) / 2;
- absolute spread;
- spread in basis points.

These are mechanical book-state measurements only.

## Depth

The engine supports two parameterized measurement families:

1. TOP_N: quote notional across the first N levels on each side.
2. BPS_BAND: quote notional inside a caller-supplied symmetric basis-point band around the mid.

**No default N and no default basis-point band are authorized.**

Any scientific target protocol must freeze the exact depth definition before target observations are opened. Choosing the definition from observed outcomes is prohibited.

## Decision-state reconstruction

Given a pre-specified anchor time and decision time, the engine may use only observations at or before the decision boundary.

It computes mechanically:

- pre-anchor book state;
- latest book state at decision;
- extreme mid observed from anchor through decision;
- maximum spread observed from anchor through decision;
- aggregate buy/sell aggressive notional in the same interval;
- decision-time MRCR continuous state vector.

Supplying a feature trade or feature book observation after the decision timestamp is an error, not something silently ignored.

## Explicit omissions

This layer does not define:

- decision clock;
- future-return horizon;
- acceptance/rejection threshold;
- continuation/reversal label;
- trade direction;
- entry/exit;
- stop/target;
- sizing;
- PnL;
- promotion.

Final boundary: **RECONSTRUCT THE STATE; DO NOT INTERPRET IT AS AN EDGE.**
