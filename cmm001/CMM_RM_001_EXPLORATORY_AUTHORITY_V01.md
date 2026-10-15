# CMM-RM-001 — CROSS-MARKET RESOLUTION MAP
## EXPLORATORY AUTHORITY V0.1 — 2026-09-25

STATUS: HYPOTHESIS-GENERATION ONLY / NO PROMOTION
PARENT: CMM-001-V01
PARENT TERMINAL STATE: INSUFFICIENT_SAMPLE
PARENT EVENT LEDGER SHA256: 8c79b4287d5a0bc7ab263b856b56bded638d75e2ea14c25434156a4eb20909d8
PARENT DAILY STATE LEDGER: CMM001_DAILY_STATE_LEDGER_V01.csv

## PURPOSE
Answer a different question from the failed/insufficient spot-fade candidate:

When an extreme cross-market gap already exists, which side moves more to close it?
- BTC spot state?
- the non-spot consensus?
- both?
- neither / divergence widens?

This is descriptive mechanism mapping, not a trading strategy and not a rescue of CMM-001.

## DATA SCOPE
Use ONLY the immutable parent CMM-001 event ledger and daily state ledger already opened under the parent authority.
No network access.
No new source download.
No 2025 or 2026 access.
No event addition/deletion/reordering.
No PnL or return variable may be used in this analysis.

## HORIZONS
For every frozen parent event date d, inspect state ledgers at:
- d+1 calendar day
- d+3 calendar days
- d+7 calendar days

If a required future daily state is absent, that event/horizon is marked unavailable; no substitution.

## DEFINITIONS
Initial gap:
G0 = S0 - N0.

For horizon h:
Gh = Sh - Nh.

Absolute gap ratio:
AGR_h = |Gh| / |G0|.

Gap shrank:
|Gh| < |G0|.

Gap crossed:
sign(Gh) != sign(G0), excluding exact zero.

Signed initial gap orientation:
sgn = +1 if G0 > 0, -1 if G0 < 0.

Spot closing contribution:
SC_h = sgn * (S0 - Sh).
Positive SC means spot moved toward the non-spot side of the original gap.

Non-spot closing contribution:
NC_h = sgn * (Nh - N0).
Positive NC means the non-spot consensus moved toward spot.

For events where the absolute gap shrank:
- SPOT_LED if SC_h > NC_h
- NONSPOT_LED if NC_h > SC_h
- TIE only if numerically equal within 1e-12.

Operational "spot-was-wrong-like" observation:
the gap shrank AND SPOT_LED.
This label is descriptive only and does not assert objective mispricing.

Component movement diagnostics:
For each available O_z, R_z and L_z at d and d+h:
component_move_toward_spot = sgn * (X_h - X_0).
Positive means that non-spot component moved toward spot under the original gap orientation.

## REQUIRED OUTPUTS
For each 1d / 3d / 7d horizon:
- valid event count
- gap shrink rate
- gap cross rate
- median and mean AGR
- median and mean fractional gap resolution = 1 - AGR
- counts/rates of SPOT_LED vs NONSPOT_LED among shrinking gaps
- unconditional spot-led-resolution rate
- unconditional nonspot-led-resolution rate
- mean/median SC and NC
- O/R/L component positive-movement rates where available
- same basic shrink / leader decomposition separately for G0>0 and G0<0, descriptive only

Also emit an event-level resolution ledger.

## GOVERNANCE
This analysis cannot:
- change CMM-001's INSUFFICIENT_SAMPLE verdict;
- promote any candidate;
- select a funding/CFTC/options/rates/stablecoin filter;
- define a new trading signal from whichever subgroup looks best;
- open 2025/2026;
- authorize live trading, micro-live, orders, exchange mutation, wallets, alerts/webhooks, Render, or merge to main.

Any new predictive hypothesis inspired by this map must get a NEW identity and be frozen before genuinely independent future evidence.

END OF AUTHORITY
