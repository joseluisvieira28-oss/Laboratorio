# POLY-COMBINATORIAL-ARB-001 — PROSPECTIVE ECONOMIC MVE V0.8

Date: 2026-09-27
Status: FROZEN_PRE_OUTCOME / PROSPECTIVE / RESEARCH_ONLY

Parent source route: SOURCE_ROUTE_PASS V0.5.
Parent failed economic pilot: V0.6 PILOT_DATA_INSUFFICIENT, immutable.
Parent source remediation: SOURCE_REMEDIATION_PASS V0.7.
No V0.6 price/book economics may be recomputed.

## 1. Hypothesis
For the already-frozen standard negative-risk events, a current public CLOB batch can occasionally expose a BUY_ALL_YES package whose guaranteed terminal package payout exceeds the executable ask-depth cost after the current first-party taker-fee formula and fixed operational buffers.

This is mechanical relative value, not prediction.

## 2. Frozen fixtures
Events:
- 32228
- 48292
- 51456

No event substitution is permitted during this MVE.

## 3. Frozen package
BUY_ALL_YES only.
q = 10 YES shares in every component market.

Terminal package payout = 10 USDC.e if every component leg is fully acquired and the standard negative-risk event resolves normally.

No SELL/short package.
No partial package economics.

## 4. Executable ask depth
One public POST /books request contains all frozen YES tokens.

For each event and each snapshot:
- require every component YES token in the batch;
- use asks only;
- sort asks ascending;
- walk visible size to exactly q=10 shares;
- insufficient visible ask size on any leg => DEPTH_INSUFFICIENT;
- no midpoint, last trade, extrapolation or imputation.

## 5. Current-state timing
V0.7 proved 25/25 REST↔WebSocket current-state compatibility, including 23 exact hashes and 2 newer WebSocket states.

Therefore V0.8 treats the single public POST /books response as one current-state observation.
Frozen transport gate:
- HTTP roundtrip <= 2000 ms;
- all frozen token books returned.

Provider per-book timestamps are preserved diagnostically only; they are NOT used as a cross-leg acquisition-clock gate.

No retroactive reinterpretation of V0.6 is permitted.

## 6. Frozen fee provenance and formula
Pinned first-party implementation:
Polymarket py-clob-client-v2 commit
292c11005d748c21342a9457d7c0ac89afc2e3f2

At run start every frozen condition ID must reproduce the exact V0.7 fd.r/fd.e descriptor. Any drift => FEE_DESCRIPTOR_DRIFT and no economics for the run.

For an ask-depth fill of s shares at price p:
platform_fee_rate = r * (p * (1-p)) ** e
platform_fee = s * platform_fee_rate

This is algebraically the pinned client BUY formula for amount=s*p, fee_slippage=0 and builder_taker_fee_rate=0.

V0.8 assumes no builder-specific fee.
No fee parameter is optimized.

## 7. Costs and margins
For every fill level:
cash ask cost = s*p
platform fee = formula above

event package total cost = sum(cash ask costs + platform fees)

raw_margin = 10 - total_cost
base_margin = raw_margin - 0.05 USDC
stress_margin = raw_margin - 0.10 USDC

The 0.05/0.10 buffers are inherited unchanged from V0.6 and were frozen before any package margin was ever computed.

## 8. Prospective observation plan
Exactly 120 scheduled attempts.
Cadence target = 1.5 seconds.
No extension, rerun or backfill based on outcome.

A snapshot is economically valid only if:
- fee descriptors match the frozen V0.7 map;
- HTTP roundtrip <=2000 ms;
- all required books are present;
- every leg is q=10 fillable.

## 9. Primary pilot adjudication
Minimum data sufficiency:
>=120 valid event-snapshots in aggregate AND >=30 valid snapshots in at least two distinct events.

If insufficient:
PILOT_DATA_INSUFFICIENT.

If sufficient and zero stress_margin > 0:
NO_IMMEDIATE_EXECUTABLE_PACKAGE_OBSERVED.

If sufficient and >=1 stress_margin > 0:
PROSPECTIVE_BOOK_EXECUTABLE_SIGNAL_OBSERVED.

This is a book-signal classification only.

## 10. Stronger descriptive gates for any positive signal
Report, but do not promote:
- number of positive stress snapshots;
- distinct events with positive stress;
- max/median positive stress margin;
- visible q=10 package cost;
- temporal clustering / consecutive-positive count;
- capital-lock diagnostic using event end date + 7 days.

One fleeting positive snapshot is NOT a diamond.

## 11. Safety and governance
Research only.
Public unauthenticated reads only.
No order signing.
No orders.
No wallet.
No capital.
No exchange mutation.
No merge to main.
No tuning after outcomes.
No rerun to seek a better result.

A positive V0.8 result would require a new independent execution-risk / one-leg-fill / persistence gate before any micro-live discussion.
