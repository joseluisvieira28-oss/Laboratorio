# MICROSTRUCTURE SCALPING LAB — DISCOVERY FREEZE V0.1

Date: 2026-09-25
Status: PRE-OUTCOME FREEZE

## Scientific partition
Historical Bybit BTCUSDT L2:
- DISCOVERY: 2023-01-18 through 2024-12-31
- OOS: 2025-01-01 through 2025-12-31
- PROTECTED HOLDOUT: 2026-01-01 onward — LOCKED

The 2026 partition MUST NOT be opened by Discovery or OOS code.

## Primary economic question
Does information observable in the L2 book at time t predict an executable future mid-price move over the frozen horizons strongly enough to remain positive after realistic transaction costs?

## Frozen horizons
- 100 ms
- 500 ms
- 1 s
- 5 s
- 15 s
- 30 s

Labels use the first observed mid-price at or after t+horizon.
No interpolation from future data is allowed.

## Causal features allowed at t
Primary:
- spread_bps
- microprice_displacement_bps = (microprice-mid)/mid * 10,000
- imbalance_l1
- imbalance_l5
- imbalance_l10

Secondary, only after implementation is causality-tested:
- signed depth-add/remove intensity
- trade aggressor imbalance
- event intensity
- short-horizon backward-looking volatility
- cross-market leader/follower state

No feature may use any event with source timestamp later than t.

## Execution model hierarchy
### Primary: taker-only
This is the first economic gate because fills are deterministic enough to model conservatively.
Entry and exit are charged taker fees plus spread/slippage/latency assumptions.

### Secondary: maker-assisted
BLOCKED until a defensible fill/queue/adverse-selection model exists.
A posted limit order MUST NOT be counted as filled merely because price touches it.

## Discovery discipline
Discovery may explore the frozen feature family only inside the Discovery partition.
Any selected rule/threshold/model must be serialized and frozen before OOS is opened.
OOS is single-pass for a frozen candidate.
No OOS rescue tuning.
2026 remains locked regardless of Discovery/OOS outcome.

## Promotion states
- SOURCE_FEASIBLE: source/replay gate passed
- DISCOVERY_SURVIVES: candidate survives Discovery after multiple-testing controls
- OOS_SURVIVES: frozen candidate survives 2025 OOS
- FORWARD_REQUIRED: historical evidence survives but target-venue forward replication is required
- NO_EDGE
- BLOCKED

None of these labels authorizes live trading.
