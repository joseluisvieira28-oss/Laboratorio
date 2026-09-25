# MICROSTRUCTURE SCALPING LAB — DISCOVERY FREEZE V0.1

Date: 2026-09-25
Status: PRE-OUTCOME FREEZE

## Scientific partition
Historical Bybit BTCUSDT L2:
- DISCOVERY: 2023-01-18 through 2024-12-31
- OOS: 2025-01-01 through 2025-12-31
- PROTECTED HOLDOUT: 2026-01-01 onward — LOCKED

The 2026 partition MUST NOT be opened by Discovery or OOS code.

## Event clock
Primary event time = matching-engine timestamp `cts` when present.
Fallback to `ts` is allowed only when `cts` is absent and must be explicitly flagged.
No future event may influence a feature timestamped at t.

## Primary economic question
Does information observable in the L2 book at time t predict an executable future move over the frozen horizons strongly enough to remain positive after realistic transaction costs?

## Frozen horizons
- 100 ms
- 500 ms
- 1 s
- 5 s
- 15 s
- 30 s

Labels use the first observed reconstructed book state at or after t+horizon.
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
- backward-looking volatility
- cross-market leader/follower state

No feature may use any event with event clock later than t.

## Frozen first Discovery MVE
- source: Bybit BTCUSDT 2023-01-18 ob500
- source window: first 250,000 messages
- anchors: at most one anchor per 1,000 ms of matching-engine time
- signals tested independently:
  - sign(microprice_displacement_bps)
  - sign(imbalance_l1)
  - sign(imbalance_l5)
  - sign(imbalance_l10)
- no threshold search in this MVE
- no parameter tuning from its outcomes
- purpose: determine whether raw predictive direction exists and whether it is remotely compatible with execution costs

## Execution labels
For each future horizon preserve:
- future mid
- future best bid
- future best ask

Taker-only executable return:
- LONG: enter at current ask, exit at future bid
- SHORT: enter at current bid, exit at future ask

Therefore spread is paid through executable BBO prices rather than subtracted twice.

## Execution model hierarchy
### Primary: taker-only
First economic gate.
Net = executable gross return - entry taker fee - exit taker fee - explicit slippage sensitivity.

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
- SOURCE_FEASIBLE
- DISCOVERY_SURVIVES
- OOS_SURVIVES
- FORWARD_REQUIRED
- NO_EDGE
- BLOCKED

None of these labels authorizes live trading.
