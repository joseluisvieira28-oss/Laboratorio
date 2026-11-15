# CMM-MECH-001 — SPOT-STATE ROLL-OFF DECOMPOSITION
## POST-OUTCOME MECHANISM AUDIT V0.1

Status: DIAGNOSTIC ONLY / ZERO PROMOTION AUTHORITY
Parent lineages:
- CMM-001-V01 = INSUFFICIENT_SAMPLE
- CMM-RM-001 = EXPLORATORY ONLY
- CMM-DRV-001-V01 = INSUFFICIENT_SAMPLE

## Purpose
Determine whether the apparent "spot-led" closure of the CMM state gap reflects actual new BTC price movement or mechanical roll-off of the trailing 7-day return state.

The parent spot raw state is:
S_raw(d) = ln(P[d] / P[d-7])

Therefore:
S_raw(d+h) - S_raw(d)
= ln(P[d+h]/P[d]) - ln(P[d-7+h]/P[d-7])

For original gap orientation s = sign(G0), oriented spot-state closure is:
s * (S_raw(d) - S_raw(d+h))
= [-s * ln(P[d+h]/P[d])] + [s * ln(P[d-7+h]/P[d-7])]

Define:
- ACTUAL_PRICE_CLOSURE = -s * ln(P[d+h]/P[d])
- ROLLOFF_CLOSURE = s * ln(P[d-7+h]/P[d-7])
- RAW_STATE_CLOSURE = ACTUAL_PRICE_CLOSURE + ROLLOFF_CLOSURE

Positive ACTUAL_PRICE_CLOSURE means BTC price itself moved in the direction that would close the original gap.
Positive ROLLOFF_CLOSURE means the historical return segment leaving the 7-day window mechanically helped close the raw spot state.

## Inputs
Use only:
1. CMM-RM-001 event-resolution identity ledger.
   Git blob SHA: 349a4227f67c316853057771784763f48a88a8fe
2. CMM-DRV-001 2025 cycle-identity ledger.
   Git blob SHA: 9414176be46ee967b63b3cc8952b53e3db4eb3bc
3. Official Binance Data Vision BTCUSDT Spot 1h archives needed only to reconstruct exact 17:00 UTC price observations from 2020-12 through 2025-12. Every archive must pass the provider CHECKSUM.

Do not read parent or child PnL/event-return ledgers.

## Required analyses
A. Parent CMM-RM 2021-2024, separately for 1d / 3d / 7d:
- valid observations
- share with ACTUAL_PRICE_CLOSURE >0
- share with ROLLOFF_CLOSURE >0
- share where |ROLLOFF_CLOSURE| > |ACTUAL_PRICE_CLOSURE|
- same metrics among events labelled SPOT_LED by the existing state-space map
- among SPOT_LED events, share where actual BTC price moved AGAINST closure despite state-space spot-led classification

B. CMM-DRV 2025 initial cycles at h=1:
- all initial cycles and confirmed-only cycles
- same actual-price vs roll-off decomposition
- report each of the three confirmed identities individually, without PnL

## Interpretation boundary
This diagnostic may explain a proxy failure but cannot:
- rescue CMM-001;
- rescue CMM-DRV-001;
- change any old verdict;
- select a new parameter or subgroup;
- grant Tier 3/Tier 2/Tier 1;
- authorize trading.

Any next predictive candidate must have a new identity and a new pre-outcome freeze.

No live trading, micro-live, orders, exchange mutation, alerts/webhooks, Render or main merge.
