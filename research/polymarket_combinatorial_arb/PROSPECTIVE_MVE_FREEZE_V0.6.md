# POLY-COMBINATORIAL-ARB-001 — PROSPECTIVE MVE FREEZE V0.6

Date: 2026-09-27
Status: FROZEN_PRE_OUTCOME / PROSPECTIVE / RESEARCH_ONLY
Parent source closeout: SOURCE_ROUTE_PASS V0.5
Parent evidence run: 36333289493
Parent artifact: 10936671674
Parent closeout commit: 987c43f245aec7c940f1ef16107ba4df69eda195

## 1. Scientific question
After this freeze, do standard non-augmented Polymarket negative-risk events ever expose a simultaneously observable, depth-fillable BUY_ALL_YES package whose fixed terminal payout exceeds the executable ask cost by enough to survive fixed operational stress buffers?

This is a contingent-claim parity test, not BTC direction prediction.

## 2. Mechanical identity
For a standard negative-risk event with N mutually exclusive and exhaustive outcomes, exactly one component YES outcome resolves true. Therefore one YES share in every component outcome has a terminal aggregate payout of exactly 1 USDC.e, subject to ordinary resolution/contract risk.

Primary package:
BUY_ALL_YES only.

No SELL/short package is tested in V0.6 because that route has separate inventory/conversion/atomicity requirements.

## 3. Frozen event fixtures
Prospective books only, after this freeze:
- 32228 — 5 outcomes
- 48292 — 7 outcomes
- 51456 — 13 outcomes

These events were selected from metadata-only source feasibility before package economics were opened. They are engineering/scientific fixtures, not post-profit selections.

## 4. Frozen trade geometry
Primary package quantity q = 10 YES shares per component outcome.

For each component token:
- use public CLOB orderbook asks only;
- sort asks by price ascending;
- walk visible depth until exactly q shares are filled;
- if cumulative ask size < q, package is NOT_FILLABLE;
- no midpoint, last trade, inferred quote, stale carry or future-nearest observation.

Package ask cost = sum of depth-walk costs across all component YES tokens.

Terminal payout = q USDC.e.

## 5. Synchronization
Use public POST /books batch request for all fixture YES tokens.
Every book must expose a provider timestamp.
A package observation is synchronized only when max(book_timestamp)-min(book_timestamp) <= 2000 ms within that event.

No timestamp-shift repair is allowed.

## 6. Fees
Fetch the public fee-rate field for every token at run start.

V0.6 computes economics only when every token in the event reports base_fee = 0.
If any component has non-zero or missing fee rate:
FEE_FORMULA_UNRESOLVED
and no package margin is computed for that event.

This avoids inventing a fee formula.

## 7. Fixed operational buffers
Because V0.6 is book-observation only and does not prove atomic fills:
- BASE operational buffer = 0.05 USDC per q=10 package.
- STRESS operational buffer = 0.10 USDC per q=10 package.

These are additive to executable ask depth and any proven fee. They are frozen before the first package sum.

Metrics:
raw_margin = q - package_ask_cost
base_margin = raw_margin - 0.05
stress_margin = raw_margin - 0.10

## 8. Capital lock diagnostic
Where event endDate is parseable:
locked_days = max(1 day, endDate + 7 calendar days - snapshot time).

The +7d is a fixed settlement-delay stress buffer.
Simple annualized stress yield may be reported as:
(stress_margin / package_ask_cost) * 365 / locked_days.

This is diagnostic only and is not used to select events or rescue a failed margin.

## 9. Prospective pilot window
Exactly 60 scheduled snapshot attempts.
Cadence target = 2 seconds.
No backfill of a missed snapshot.
No extending the run because a profitable observation did not occur.

## 10. Pilot adjudication
This pilot cannot promote, Tier-rank or authorize capital.

Data sufficiency:
>=60 synchronized, fee-resolved, q-fillable event-snapshots in aggregate.

If insufficient:
PILOT_DATA_INSUFFICIENT.

If sufficient and >=1 observation has stress_margin > 0:
PROSPECTIVE_BOOK_EXECUTABLE_SIGNAL_OBSERVED.

If sufficient and zero observations have stress_margin > 0:
NO_IMMEDIATE_EXECUTABLE_PACKAGE_OBSERVED.

Neither zero-result state is NO_EDGE because the pilot is short and observations are serially dependent.

## 11. Mandatory outputs
Per event:
- attempted / valid synchronized snapshots;
- q-fillable snapshots;
- fee-resolved state;
- positive raw/base/stress counts;
- max raw/base/stress margin;
- median stress margin;
- maximum timestamp dispersion;
- locked-days diagnostic when available.

Aggregate:
- valid event-snapshots;
- positive stress observations;
- distinct events with positive stress observations;
- pilot adjudication.

## 12. Hard prohibitions
No authenticated endpoints.
No orders.
No wallet.
No capital.
No exchange mutation.
No midpoint economics.
No threshold tuning.
No event substitution after seeing margins.
No extension of 60 attempts based on result.
No main merge.

## 13. What a positive result would mean
Only that a mechanically coherent, prospective, public-book package mispricing was observed after fixed depth and fixed buffers.

It would NOT prove:
- actual multi-leg fill;
- atomic execution;
- persistence;
- scalable capacity;
- Tier 2 / quasi-diamond / diamond;
- live-trading readiness.

Those require separate prospective tests.
