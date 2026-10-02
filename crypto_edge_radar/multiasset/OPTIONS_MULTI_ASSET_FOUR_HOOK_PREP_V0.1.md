# OPTIONS MULTI-ASSET — FOUR-HOOK PREPARATION V0.1

Date: 2026-10-02  
Branch: `options-multiasset-fourhook-prep-v0.1-2026-10-02`  
Base: `options-v21-futures-only-autolive-v02-2026-09-25`  
Status: PREPARATION_ONLY / RESEARCH-ONLY / NO NEW LIVE AUTHORITY

## Operator concept

One OPTIONS supervisor ("one rod") may observe four independent hooks:

1. BTC options -> BTC_USDT perpetual
2. ETH options -> ETH_USDT perpetual
3. SOL options -> SOL_USDT perpetual
4. XRP options -> XRP_USDT perpetual

Each hook owns its own immutable scientific identity, source evidence, signal state, forward evidence and execution-feasibility state.

The four hooks share infrastructure, not scientific credit.

## Hard scientific boundary

BTC keeps the existing frozen OPTIONS-SPOTPERP-001-V2.1 identity. Nothing in this branch changes its signal, sign, horizon, risk scaling, historical result, forward evidence or live authority.

ETH, SOL and XRP are NEW hypotheses. They MUST NOT inherit BTC's scientific status, promotion tier, expected return, thresholds or performance claims.

Before any historical outcome is opened for ETH/SOL/XRP, each hook requires its own prospectively committed freeze covering at least:

- option source and instrument convention;
- exact eligible DTE range;
- exact call and put moneyness bands;
- minimum distinct instruments per side;
- IV aggregation rule;
- signal sign rule;
- futures outcome alignment;
- entry and exit boundary;
- cost model;
- risk scaling;
- development window;
- protected OOS/holdout window;
- pass/fail gates.

No post-outcome tuning is allowed.

## Execution architecture target

All four hooks target MEXC USDT perpetuals for execution translation:

- BTC -> BTC_USDT
- ETH -> ETH_USDT
- SOL -> SOL_USDT
- XRP -> XRP_USDT

Directions are symmetric:

- +1 -> LONG perpetual
- -1 -> SHORT perpetual

No Spot balance is required by the target architecture.

The existing BTC futures-only implementation is the reference execution transport. Reuse of infrastructure does not imply reuse of scientific evidence.

## Shared supervisor semantics

The target supervisor may poll all four sources concurrently.

Initial execution risk policy is intentionally conservative:

- one shared global real-money position slot;
- all four shadow/forward lanes continue observing even while the slot is occupied;
- if more than one executable signal is due for the single slot, arbitration is deterministic;
- losing due real-money signals are NO_CHASE but remain recorded as scientific shadow observations;
- no signal may be transformed into another asset or direction to obtain execution.

A later authority may explicitly raise the global position limit only after a separate portfolio-risk freeze. This preparation does not do so.

## Capital feasibility

Execution feasibility is dynamic and venue-specific.

Each hook must run a fresh preflight at signal time for:

- contract availability;
- contract size;
- minimum volume;
- volume step;
- current reference price;
- isolated margin support;
- required position mode;
- account fees;
- funding;
- available balance;
- resulting minimum executable notional versus the frozen micro-live cap.

If the venue minimum exceeds the cap, the hook is CAPITAL_FEASIBILITY_BLOCKED for real-money execution. Its research/forward observation continues.

No cap is increased automatically to rescue a blocked hook.

## Source model

The registry marks the intended options-source family as Deribit for BTC, ETH, SOL and XRP, but this is only a preparation binding.

Each new asset still requires a Source/Data Gate proving that the required historical and prospective fields are available with defensible provenance and without leakage.

Differences between inverse and linear option conventions must be handled explicitly by the asset adapter and must not be silently normalized.

## Safety / authority

This branch:

- creates no orders;
- changes no exchange state;
- does not arm live trading;
- creates no new live authority;
- does not merge to main;
- does not alter BTC V2.1 science;
- does not open protected ETH/SOL/XRP outcomes.

## Prepared implementation pieces

- `options_multiasset_registry_v01.json`: canonical hook identities and venue/source bindings.
- `radar/options_multiasset_registry.py`: deny-by-default registry validator and signal-route resolver.
- `tests/test_options_multiasset_registry.py`: invariants proving four independent hooks, futures-only routing and symmetric LONG/SHORT mapping.

## Next legitimate gates

1. Source capability probe for ETH, SOL and XRP options.
2. Per-asset PRE-OUTCOME scientific freeze.
3. Historical Source/Data Gate.
4. Development evaluation.
5. Independent OOS/holdout if predeclared gates permit it.
6. Prospective shadow.
7. Only then: candidate-specific micro-live authority for any surviving hook.

Until those gates pass, BTC is the only hook with inherited operational history. ETH/SOL/XRP are prepared, not promoted.
