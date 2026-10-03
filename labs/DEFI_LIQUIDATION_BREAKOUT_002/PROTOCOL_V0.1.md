# DEFI-LIQUIDATION-BREAKOUT-002 — V0.1

Date: 2026-10-03
Status: FROZEN PRE-DEVELOPMENT / 2026 FINAL HOLDOUT SEALED
Branch: dls-liquidation-breakout-002-v0.1

## Parent findings
DEFI-LIQUIDATION-SHOCK-001 established a robust direction-agnostic fact:
completed SOL-collateral liquidation cascades are followed by materially larger short-horizon absolute moves than matched controls.

Its frozen SHORT translation then failed the protected 2025 economic holdout:
- 3,233 serialized trades
- 100% source/market coverage
- mean gross short return approximately -0.4 bps
- mean net at 26 bps approximately -26.4 bps
- bootstrap primary-net CI entirely negative
- 0/3 inferential protocol families positive

Therefore this new lab does NOT invert SHORT to LONG.
It tests a materially different causal translation: wait for the market itself to reveal the first-minute direction, then test continuation.

## Scientific identity
Lab ID: DEFI-LIQUIDATION-BREAKOUT-002

Question:
after a qualifying SOL-collateral liquidation cascade, does the first complete minute after signal availability reveal a short-lived continuation direction that remains economically positive after current execution costs?

## Frozen source events
Same source-event semantics only:
- SOL collateral target mint
- 60-second quiet-period clustering
- same protocol/class authority as parent
- no source threshold or event severity filter

Development source:
1. canonical 2021-2024 parent census:
   run 36465385517 / artifact 10988887983
   artifact SHA256 7703f53869df186d20cf5c339327a1df2ee3f433c7ff0f8e6a02e1b9d053d97c
   census SHA256 0a10bf5ff4d7ad41f4764c4c1eb592c28f25b01b0a854b144944adf46363d46b
2. canonical protected-2025 source authority:
   run 37134450131 / artifact 11277791628
   artifact SHA256 738414881490b9232354f800893d10410d36b60f87fc2db5e5bb983e46c21ae4
   census SHA256 f89889c2b2f184e54ddd8b0ba83cfce47d75b0e5ba59c8fd863cbe8e0051717c

Development years: 2021-2025 inclusive.

2026 is SEALED and may be opened only if development passes every gate.
Frozen final holdout interval:
2026-01-01T00:00:00Z <= source event timestamp < 2026-09-28T00:00:00Z.

## Frozen timing and direction
For every eligible cluster with source T0:

E0 = first exact UTC minute boundary strictly after T0.
P0 = SOLUSDT 1m OPEN at E0.

E1 = E0 + 1 minute.
P1 = SOLUSDT 1m OPEN at E1.

The first-minute confirmation return is:
C1 = (P1 / P0) - 1.

Direction:
- C1 > 0 => LONG
- C1 < 0 => SHORT
- C1 == 0 => NO TRADE

Entry:
exact 1m OPEN at E1.

Exit:
X = E0 + 5 minutes.
exact 1m OPEN at X.

Thus the position is held for four minutes after the one-minute confirmation.

No threshold on |C1|.
No alternative confirmation duration.
No source-side direction.
No reversal branch.
No stop, target, trailing rule or adaptive exit.

## Frozen gross return
If LONG:
R_gross = (P_exit - P_entry) / P_entry

If SHORT:
R_gross = (P_entry - P_exit) / P_entry

Equivalent:
R_gross = sign(C1) * (P_exit - P_entry) / P_entry

## Market source
Binance Spot SOLUSDT 1m public archives from data.binance.vision.
Every used daily ZIP requires official CHECKSUM match.
Exact UTC minute OPEN only.
No nearest-bar reconstruction.

For development, no bar at/after 2026-01-01 may be read.

## Current execution costs
Intended eventual execution translation remains automated MEXC SOL_USDT perpetual.
Inherit the already-frozen current cost authority without reduction:

PRIMARY = 26 bps round trip
- 16 bps MEXC API taker fee floor
- 10 bps fixed execution/funding reserve

STRESS = 40 bps round trip.

No maker fills, rebate, VIP discount or fee rescue.

R_primary = R_gross - 0.0026
R_stress  = R_gross - 0.0040

## Serialization
Sort trade candidates by E1, then cluster_id.

Accept first eligible trade.
While a trade is open, suppress any candidate with E1 < current X.
A candidate with E1 == X is eligible.

No pyramiding.
No overlap.

## Development sample and gates
Development uses every valid 2021-2025 source cluster under the rule above.

Minimum evidence:
- source/market coverage >=95%
- serialized trade N >=3,000
- at least 250 UTC calendar days with trades
- all five calendar years represented
- at least three protocol families with >=100 serialized trades each

DEVELOPMENT_BREAKOUT_SURVIVES requires ALL:
1. mean R_primary > 0
2. UTC-day block-bootstrap 95% CI lower bound of mean R_primary > 0
3. mean R_stress > 0
4. primary profit factor >=1.10
5. at least 4 of 5 yearly mean R_primary values > 0
6. at least 3 protocol families with >=100 trades have positive mean R_primary
7. no single UTC day contributes >25% of total positive primary-net PnL
8. no single calendar year contributes >40% of total positive primary-net PnL

Bootstrap:
- UTC source-T0 day blocks
- 5,000 repetitions
- percentile 95% CI
- deterministic seed = SHA256 integer of:
  DEFI-LIQUIDATION-BREAKOUT-002 + "development-2021-2025" + "1m-confirm-4m-hold" + "V0.1"

If valid data but any gate fails:
NO_EDGE_DEVELOPMENT_BREAKOUT

If source/integrity/coverage fails:
SOURCE_BLOCKED_DEVELOPMENT_BREAKOUT

## Frozen 2026 final holdout
2026 opens only if development classification is DEVELOPMENT_BREAKOUT_SURVIVES.

Exact same:
- event source semantics
- E0/E1/X
- first-minute sign
- 4-minute hold
- 26/40 bps costs
- serialization
- market field
- bootstrap implementation

Minimum:
- >=500 serialized trades
- >=95% source/market coverage
- >=60 UTC days
- at least two protocol families with >=100 trades

SURVIVES_2026_FINAL_BREAKOUT requires ALL:
1. mean R_primary > 0
2. bootstrap 95% CI lower bound > 0
3. mean R_stress > 0
4. primary profit factor >=1.10
5. at least two protocol families with >=100 trades have positive mean R_primary
6. no single UTC day contributes >25% of total positive primary-net PnL
7. no single calendar month contributes >40% of total positive primary-net PnL

Otherwise:
NO_EDGE_2026_FINAL_BREAKOUT

## Anti-rescue
After development prices open:
- no C1 threshold
- no confirmation duration change
- no 2m/3m/5m confirmation
- no exit horizon change
- no LONG-only or SHORT-only rescue
- no protocol subset
- no year subset
- no volatility/session/news filter
- no source-severity filter
- no fee reduction
- no maker assumption
- no alternate venue
- no stop/target optimization
- no 2026 opening after failed development

Any changed design requires a new identity and untouched evidence.

## Authority
Research only.
No live trading.
No orders.
No wallet/exchange mutation.
No merge to main.
Trading authority: NONE.
