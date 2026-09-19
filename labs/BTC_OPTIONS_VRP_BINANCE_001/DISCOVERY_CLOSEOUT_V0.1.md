# BTC-OPTIONS-VRP-BINANCE-001 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-19
MVE: `BOVRP-ATM30-24H-STRADDLE-CARRY-001`
Canonical run: `35466347103`
Canonical head: `2db0f9ec3d1b0d227e903f49ad5a1f745bd5eb74`
Artifact ID: `10591731438`
Artifact digest: `sha256:de049b25da55e6d64a7eff91620050dfd668f5bece27e906ed45349d186c4ad6`

## Final verdict

**DISCOVERY_FAIL_NO_PROMOTION**

Primary frozen stratum: 15 <= DTE < 31, target 30 DTE, 08:00 UTC to +24h, executable short ATM straddle using entry bid and exit ask, with frozen regular-user option fees.

Results:
- N = 111
- mean net premium return = -4.9591%
- median net premium return = -2.5619%
- profit factor on net PnL = 0.18195
- bootstrap 95% CI for mean = [-7.11895%, -3.05012%]
- positive months = 0
- leave-one-month-out positive count = 0

Frozen gates:
- N >= 80: PASS
- mean > 0: FAIL
- median > 0: FAIL
- profit factor > 1: FAIL
- bootstrap lower bound > 0: FAIL
- positive months >= 4: FAIL
- leave-one-month-out positive count >= 5: FAIL

## Scientific interpretation

This free Binance 2023 24h executable short-vol implementation does not support promotion. The negative result is broad rather than marginal: the mean and median are negative, PF is far below 1, the entire bootstrap interval is below zero, no represented month is positive, and every leave-one-month-out mean remains non-positive.

This is not a verdict that all BTC variance-risk-premium mechanisms are absent. It is a verdict against this exact prospectively frozen Binance execution MVE.

The existing Deribit statistical Discovery `DISCOVERY_PASS_VRP_EXISTS` remains scientifically distinct and unchanged. This Binance MVE must not be used to rewrite or rescue the Deribit lineage.

## Stop rule

Do not rescue this MVE by:
- changing the primary DTE bucket;
- choosing the 8-15 or 2-4 DTE secondary strata after seeing the primary outcome;
- changing hold time, decision hour or target DTE;
- using mid/mark prices;
- changing fees;
- adding/removing delta hedge;
- selecting another normalization;
- changing bootstrap/month gates;
- inverting the trade direction.

Any future Binance-options hypothesis must be materially new, separately justified, and prospectively frozen.

No live trading, exchange mutation, wallet access, 2025/2026 access, or merge to main occurred.
