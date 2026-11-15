# CMM-MECH-001 — SPOT-STATE ROLL-OFF AUDIT V0.1

**Status: DIAGNOSTIC ONLY — NO PROMOTION**

This audit reads no parent/child PnL ledger. It decomposes the trailing 7-day spot-state change into actual new BTC price movement versus the historical return segment rolling out of the window.

## Parent state-space SPOT_LED — 1d
- N: 15
- Actual BTC price supported closure: 80.00%
- Roll-off supported closure: 86.67%
- |roll-off| > |actual price move|: 60.00%
- State-space SPOT_LED while actual price moved against closure: 20.00%

## Parent state-space SPOT_LED — 3d
- N: 21
- Actual BTC price supported closure: 52.38%
- Roll-off supported closure: 100.00%
- |roll-off| > |actual price move|: 80.95%
- State-space SPOT_LED while actual price moved against closure: 47.62%

## Parent state-space SPOT_LED — 7d
- N: 26
- Actual BTC price supported closure: 57.69%
- Roll-off supported closure: 96.15%
- |roll-off| > |actual price move|: 84.62%
- State-space SPOT_LED while actual price moved against closure: 42.31%

## 2025 dynamic confirmed cycles — first 24h
- N: 3
- Actual BTC price supported closure: 66.67%
- Roll-off supported closure: 66.67%
- |roll-off| > |actual price move|: 33.33%

## Interpretation boundary
This can diagnose whether the spot-state proxy is mechanically contaminated. It cannot rescue any strategy or create a new signal from favorable subgroups.
Any next candidate requires a new pre-outcome freeze.
