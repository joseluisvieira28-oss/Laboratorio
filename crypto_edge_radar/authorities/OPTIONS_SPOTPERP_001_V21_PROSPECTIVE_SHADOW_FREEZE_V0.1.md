# OPTIONS-SPOTPERP-001 / V2.1 — PROSPECTIVE SHADOW FREEZE V0.1

**Freeze time:** 2026-09-17T20:20:25Z  
**Scientific authority:** `options-spotperp-001-v21-oos-2025-v01`  
**V3 status:** Tier 2 / Quase Diamante / high-risk fragility  
**Purpose:** start genuinely prospective read-only shadow evidence without changing the promoted V2.1 rule.

## Immutable rule

No scientific parameter changes are authorized.

- signal: `CALL_IV_MINUS_PUT_IV`;
- call universe: strike/index 1.05–1.20, DTE 30–120 days;
- put universe: strike/index 0.80–0.95, DTE 30–120 days;
- instrument-day IV aggregation: median transaction IV;
- minimum five distinct valid instruments per side;
- side aggregation: median instrument-day IV;
- direction: positive signal = LONG, negative = SHORT, zero = FLAT;
- historical execution identity: BTCUSDT spot, 00:00 UTC t+1 to 00:00 UTC t+2;
- volatility state: BTCUSDT daily close-to-close log return, RV20;
- baseline: expanding median of every valid RV20 through signal date t;
- minimum valid RV20 history: 60;
- weight: `min(1.0, expanding_median_RV20_t / RV20_t)`;
- leverage above 1.0: forbidden;
- BASE cost: 10 bps full-notional, linearly scaled by weight;
- STRESS cost: 20 bps full-notional, linearly scaled by weight.

## Prospective boundary

Only signal dates and hypothetical entries whose information becomes available **strictly after 2026-09-17T20:20:25Z** may count as new prospective shadow evidence.

No pre-boundary 2026 trade, return, PnL or outcome may be counted, reported, selected, excluded, promoted or used to tune the rule.

## State-bootstrap amendment

A deterministic state bootstrap is allowed after this freeze solely because V2.1 requires lagged historical state to evaluate future signals.

Allowed bootstrap inputs:
- Deribit public BTC option trades before the boundary, only to reconstruct the exact signal-state machinery required for the first post-boundary signal;
- BTCUSDT daily closes before the boundary, only to reconstruct RV20 and the expanding-median state;
- the already frozen pre-2026 history may be reused exactly as previously defined.

Forbidden during bootstrap:
- future-return calculation;
- PnL calculation;
- quarterly/yearly performance statistics;
- parameter selection;
- threshold/filter/horizon/direction/subgroup changes;
- deletion of an observation because of its later outcome;
- use of 2026 bootstrap history as a new retrospective validation sample.

The bootstrap must output a hashable state receipt with source range, row/trade counts, last accepted timestamps and state values. That receipt is operational provenance only.

## Prospective iteration contract

For each eligible post-boundary signal date:
1. use only information available under the original V2.1 construction;
2. compute the exact V2.1 signal and weight;
3. timestamp the planned BTCUSDT spot entry/exit before the outcome is known;
4. record the shadow intent append-only;
5. after the frozen exit time, reconcile the public market outcome, fees and slippage assumptions without changing the intent;
6. preserve losers, winners, flats, source failures and missed observations alike.

## Deployment

- shadow/research only;
- no authenticated exchange API required by this freeze;
- no exchange mutation;
- no order creation/cancel;
- no wallet operation;
- no leverage;
- no automatic live activation;
- no merge to main;
- no Tier-1 claim from this freeze alone.

Any future micro-live route requires a separate candidate-specific risk/execution authority after the source adapter, state provenance and implementation mapping pass their gates.
