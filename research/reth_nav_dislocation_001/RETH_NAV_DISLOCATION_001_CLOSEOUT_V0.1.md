# RETH-NAV-DISLOCATION-001 — CLOSEOUT V0.1

Final classification: **DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE**

## What passed

- Historical source gate: PASS.
- Split transport / EIP-1898 blockHash provenance: PASS.
- 3/3 fixed equivalence blocks had identical PublicNode and BlockMachine block hashes.
- 12/12 scientific return comparisons matched exactly across direct, Multicall-by-number and Multicall-by-blockHash.
- Dense calibration census: 556/556 valid, 0 invalid.
- Frozen q05/q95 calibration: PASS.

Calibration thresholds:
- q05 = -7,390,227 ppb (~-0.7390%).
- q95 = +5,729,902 ppb (~+0.5730%).

Calibration state counts:
- DISCOUNT_EXTREME = 28.
- NEUTRAL = 500.
- PREMIUM_EXTREME = 28.

## Discovery predictor gate

Frozen Discovery grid:
- 139/139 state points valid.
- 0 source errors.
- boundary predecessor valid and NEUTRAL.

Observed Discovery states:
- DISCOUNT_EXTREME = 0.
- NEUTRAL = 139.
- PREMIUM_EXTREME = 0.

Discovery predictor range:
- minimum ≈ -0.5830%.
- maximum ≈ +0.0635%.

Therefore neither frozen q05 nor q95 threshold was crossed anywhere in the Discovery predictor grid.

Transition-entry events:
- total = 0.
- discount = 0.
- premium = 0.

Frozen minimum required:
- >=30 total;
- >=10 discount;
- >=10 premium.

Result:
**DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE**

## Scientific interpretation

The data/source problem was solved. The exact predictor definition was reconstructible and fully block-pinned.

However, the pre-frozen extreme-state definition generated no Discovery events in the pre-frozen Discovery region. The mechanism hypothesis therefore cannot be tested under this exact lab design without changing the state definition or sample construction after seeing the predictor distribution.

That rescue is forbidden.

## Boundaries preserved

The following were never opened:
- future dislocation outcomes;
- market returns;
- mechanism Discovery;
- OOS;
- protected holdout;
- PnL;
- live trading.

Promotion credit: 0.

## Resolution

Close the exact lab **RETH-NAV-DISLOCATION-001**.

Do not:
- widen q05/q95;
- switch to q10/q90 or another quantile;
- change cadence to manufacture events;
- change de-clustering;
- switch pool;
- use the +21,600-block diagnostic;
- open outcomes anyway.

A future attempt must be a scientifically distinct child hypothesis frozen before its data are opened.
