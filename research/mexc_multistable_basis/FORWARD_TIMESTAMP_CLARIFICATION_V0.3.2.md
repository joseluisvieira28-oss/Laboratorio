# MEXC-MULTI-STABLE-BASIS-001 — FORWARD TIMESTAMP CLARIFICATION V0.3.2

Date: 2026-10-07
Status: TECHNICAL SEMANTICS / PRE-OUTCOME

Parent authority:
- PROSPECTIVE_PREOUTCOME_FREEZE_V0.3.md
- CALIBRATION_THRESHOLD_RECEIPT_V0.3.md

No prospective economic outcome has been opened before this clarification.

Closed-candle timestamp convention:
- raw MEXC Contract and Spot 1m K-lines are keyed by minute OPEN timestamp `s`;
- that bar becomes economically observable only at close timestamp `t = s + 60 seconds`;
- V0.3 forward signal timestamp is `t`, the close/observable timestamp;
- all signal inputs use the bar whose raw open timestamp is exactly `t-60`;
- entry timing 0–30 seconds is measured from `t`;
- exit due time is exactly `t + 15 minutes`.

The calibration q99 distribution is unchanged because this is a one-minute relabeling of observability time, not a change to prices, sample membership, threshold rule or economic horizon.

Prospective boundary:
Signal close timestamp `t` must be strictly later than threshold-receipt commit time
`2026-10-07T15:44:50Z`.

No backfill of any already-closed eligible minute before the collector actually becomes live.
