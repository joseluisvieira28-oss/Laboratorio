# CRYPTO EDGE RADAR — TOMORROW ON CHECKLIST V1

Purpose: make the machine operationally ready without manufacturing a trade.

## Already prepared

- aggressive deployment policy frozen;
- current candidate registry separated from old historical labels;
- Tier 4 capital block;
- Tier 3 shadow-only gate;
- Tier 1/2 micro-live eligibility gate;
- default account risk envelope: 0.10% / trade, 0.30% concurrent, 0.30% daily stop, 0.75% weekly stop;
- advisory stop-based position sizing helper;
- exact pure signal trap for ETF-CME-INSTFLOW-001 using CFTC code 133741;
- no authenticated exchange API, wallet, order, cancel or mutation path.

## Required before first real-money execution

1. Record current deployable account equity used for sizing.
2. Select and freeze the execution venue.
3. Select and freeze the exact execution instrument.
4. Confirm whether the instrument supports the frozen LONG and SHORT states without changing the scientific signal.
5. Record actual maker/taker fees and realistic slippage assumption.
6. Freeze the strategy-specific maximum-loss/exposure model.
7. Confirm that the proposed trade fits the account-level risk envelope.
8. Generate a pre-trade receipt before manual execution.
9. User manually confirms/executes the order; the radar itself has no order path.
10. Record actual fill, fees and slippage immediately after execution.

## ETF-CME-INSTFLOW-001 specific blocker

The historical strategy uses a 7-day sign position and has no frozen stop. Therefore the generic 0.10% stop-risk formula cannot be applied honestly yet. Before capital deployment, the exact real-money instrument and a prospective exposure/max-loss contract must be frozen.

This is an execution-risk blocker, not a new scientific rejection. Shadow monitoring can remain active.

## Signal discipline

- no entry without an exact frozen signal;
- no chasing after the entry window;
- no discretionary inversion;
- no extra filters added because of current market conditions;
- no martingale or recovery sizing;
- no increasing size after wins during the initial validation block;
- no rescue of Tier 4 strategies;
- no promotion of a secondary/post-hoc survivor into live capital without prospective re-certification.

## First-session output

For every candidate the radar should show one of:

- `NO_SIGNAL`
- `SHADOW_SIGNAL`
- `BLOCKED_SIGNAL` + exact blocker
- `MICRO_LIVE_ELIGIBLE` + advisory risk budget + execution receipt template

The first objective is clean real execution evidence, not maximum PnL.
