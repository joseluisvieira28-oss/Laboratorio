# MEXC WTI ATTACK — CONSOLIDATED CLOSEOUT V1.2–V1.8

Date: 2026-10-04
Scope: research-only
Main: unchanged
Live trading: none
Orders: none

## 1. Source authority — PASS

MEXC:
`USOIL_USDT` / OIL(WTI)

Official event authority:
U.S. EIA Weekly Petroleum Status Report

Current public MEXC metadata snapshot:
- maker 0
- taker 0.0001 per side
- index origins include HYPERLIQUID

Hyperliquid binding:
`xyz:CL` = Crude Oil (WTI)

Targeted source verdict:
`HYPERLIQUID_WTI_SOURCE_PASS__XYZ_CL`

## 2. EIA price-shock family

V1.3 Min1:
`SOURCE_BLOCKED_WTI_MIN1_HISTORICAL_RETENTION__NO_SCORING`

V1.4 Min5:
35/35 event windows usable.
32 frozen continuation/reversal cells.
Pre-Holm eligible: 0.

Verdict:
`NO_WTI_EIA_EVENT_SHOCK_OOS_SURVIVOR_AT_FROZEN_V14_GATE`

## 3. EIA fundamental inventory family

Official EIA series:
`WCESTUS1`

30/30 releases mapped and 30/30 MEXC windows usable.

Frozen direction:
DRAW => LONG
BUILD => SHORT

12 frozen threshold/horizon cells.
Pre-Holm eligible: 0.

Verdict:
`NO_WTI_EIA_FUNDAMENTAL_DISCOVERY_CANDIDATE_AT_FROZEN_V15_GATE`

## 4. Hyperliquid cross-venue family

Source:
MEXC `USOIL_USDT` ↔ Hyperliquid `xyz:CL`

V1.7:
historical source retention began only 2026-10-01 00:15 UTC.
No scoring.

V1.8 source-valid window:
- 2,865 Discovery overlap minutes
- 1,981 OOS minutes available
- 64 frozen lead/lag cells
- pre-Holm eligible: 1
- Holm-selected: 0
- OOS opened: NO

Verdict:
`NO_WTI_CROSSVENUE_OOS_SURVIVOR_AT_FROZEN_V18_GATE`

## 5. Best descriptive near-cell

NOT a candidate:
- HL shock >=5 bps
- MEXC underreaction >=5 bps
- horizon 1m
- N=42
- wins=26
- win rate=61.90%
- gross mean=+3.525 bps
- p=0.0821
- all three chronological thirds positive
- illustrative net after current 2 bps fee-only hurdle=+1.525 bps

It failed frozen N>=50 and was not Holm-eligible.

Any future revisit must be prospective/future-forward only.

## Overall WTI verdict

No WTI diamond was found in the frozen retrospective families.

What survived:
- strong public data infrastructure;
- exact MEXC↔Hyperliquid WTI binding;
- low current MEXC fee snapshot relative to other Global Asset routes;
- one interesting but underpowered descriptive cross-venue cell.

What did NOT survive:
- EIA post-release continuation/reversal;
- simple EIA commercial crude BUILD/DRAW direction;
- frozen short-history Hyperliquid→MEXC underreaction family.

Scientific status:
`NO_PROMOTABLE_WTI_EDGE__SOURCE_INFRASTRUCTURE_VALID__ONE_FORWARD_ONLY_NEAR_CELL`

No merge to main.
No live trading.
No accounts.
No orders.
No post-outcome rescue.
