# BINANCE-DUAL-PRECURSOR-SPOT-HAZARD-003 — V0.1 PRE-OUTCOME DISCOVERY FREEZE
Date: 2026-10-05
Status: FROZEN BEFORE FULL DEVELOPMENT CENSUS / MARKET-OUTCOME ANALYSIS

## Economic hypothesis
Binance publicly describes Binance Alpha as a pre-listing token selection pool for Binance Exchange.

A second official Binance product signal — the launch/announcement of a Binance Futures perpetual contract — may materially increase the near-term hazard of a later Binance Spot listing for an Alpha token.

The public state:
ALPHA_PRESENT + FUTURES_PERPETUAL_PRESENT + NOT_YET_BINANCE_SPOT
is the frozen DUAL PRECURSOR state.

This is a distinct economic hypothesis from post-announcement listing-reaction trading.

## Development and holdout
- Development period: 2025 only.
- 2025 is explicitly discovery/development, not confirmatory.
- 2026 remains CLOSED and MUST NOT be inspected for outcome validation during V0.1.
- Any 2025 result can only nominate a candidate.
- A separate pre-outcome freeze is mandatory before opening 2026.

## Universe construction
Build the universe from ALL identifiable Binance Alpha tokens in the 2025 development period, not from later Spot-listed tokens.

For each token, mechanically determine:
1. first defensible public Binance Alpha presence timestamp;
2. first official Binance Futures perpetual announcement timestamp, if any;
3. whether Binance Spot listing already existed at that time;
4. later first official Binance Spot listing announcement timestamp, if any.

No token may be included because it later listed on Spot.
No token may be excluded because it did not list on Spot.

Identity must be resolved by contract address when available, otherwise exact project+ticker evidence. Ambiguous ticker collisions are excluded with reason.

## Primary exposure
A token enters the DUAL PRECURSOR cohort at:
T_DUAL = max(first Alpha presence timestamp, first Binance Futures perpetual announcement timestamp)
provided the token is not already Binance Spot-listed at T_DUAL.

## Control cohort
Alpha tokens that are not Binance Spot-listed and have NOT entered the dual-precursor state at the corresponding observation boundary.

Controls are required; a spot-success-only sample is forbidden.

## Primary prediction endpoint
From T_DUAL, measure whether first Binance Spot listing announcement occurs within:
- 7 calendar days PRIMARY
- 30 calendar days SECONDARY
- 90 calendar days SECONDARY

Primary statistical quantity:
7-day Spot-listing hazard/rate for DUAL PRECURSOR versus eligible ALPHA-ONLY controls.

Report:
- n dual
- n controls
- 7d spot-list count/rate
- 30d count/rate
- 90d count/rate
- absolute risk difference
- risk ratio when defined
- Fisher exact p-value where sample permits
- median time-to-spot among successes
- unresolved/censored observations

## Primary discovery gate — ALL required
- >=12 eligible DUAL PRECURSOR observations in 2025
- >=24 eligible ALPHA-ONLY controls or all available controls if census proves fewer
- DUAL 7-day Spot-list rate >=25%
- DUAL 7-day rate at least 3x ALPHA-ONLY 7-day rate
- absolute 7-day rate difference >=15 percentage points
- leave-one-out dual 7-day rate remains >=20%
- no single calendar month contributes >35% of DUAL successes

If insufficient source/census support -> SOURCE_BLOCKED.
If sample exists but any primary gate fails -> NO_PREDICTIVE_EDGE_DISCOVERY.
If all gates pass -> SURVIVES_PREDICTIVE_DISCOVERY.

## Market layer — SECONDARY, NON-GATING in V0.1
Only after the full outcome-independent universe and event timestamps are frozen may market prices be opened.

For tokens already trading on a frozen external public venue before T_DUAL, report gross external-market returns from the first complete minute after T_DUAL:
- +1h
- +6h
- +24h
- +7d

Also report BTC-relative returns and MFE/MAE.

No market-return metric can rescue a failed primary prediction gate in V0.1.

## If prediction discovery survives
Before any tradability claim:
1. create a NEW pre-outcome market-execution freeze;
2. freeze external venue bindings;
3. freeze entry delay, spread/slippage/cost model, exit mechanism and risk limits;
4. only then open a still-unseen confirmatory period.

## Anti-hindsight
After this freeze:
- no changing the DUAL definition;
- no selecting only Spot winners;
- no changing 7d primary horizon;
- no lowering gates;
- no removing losers/outliers;
- no reclassifying Alpha/Futures timestamps based on outcomes;
- no 2026 outcome inspection;
- no post-outcome tuning.

## Governance
Research-only.
Public data only.
No trading.
No orders.
No authenticated/private endpoints.
No account reads.
No wallets.
No exchange mutation.
No merge to main.
