# MEXC SESSION-WIDE SHOCK CLUSTER — PRE-OUTCOME FREEZE V1.3

Date: 2026-10-05
Status: FROZEN BEFORE V1.3 OUTCOMES

Purpose:
Test a session-wide, event-conditioned catch-up mechanism with shock magnitude intentionally large enough to have a plausible path through the documented standard MEXC API fee floor.

Historical window:
- 2026-08-10 through 2026-09-08
- source anchors 2026-08-17, 2026-08-31, 2026-09-08 are excluded from outcomes
- only candidates passing the V1.2 source gate on all anchors are eligible
- candidate selection is source-only and cannot depend on outcomes

Frozen event definition:
- 5-minute external return = mean(Binance, Bitget)
- abs(external 5m return) >= 50 bps
- lag gap = external 5m return - MEXC 5m return
- lag gap must have the same sign as the external move
- abs(lag gap) >= 25 bps
- direction = FOLLOW_EXTERNAL_CONSENSUS
- entry at trigger timestamp
- exit 5 minutes later

Scientific unit:
- one UTC timestamp cluster
- all assets triggering at the same timestamp are equal-weighted into one cluster return
- global 5-minute cooldown after any accepted cluster
- no overlapping cluster outcome windows

Scientific PASS:
- >=20 clusters
- >=8 triggered UTC dates
- mean cluster gross >0
- median cluster gross >0
- cluster win rate >50%
- both chronological half means >0
- exact one-sided binomial p<0.05

Operational PASS:
- scientific PASS
- mean net after 16 bps >0
- median net after 16 bps >0

No threshold grid, horizon grid, asset-specific tuning, retrospective rescue, private endpoints, account reads, orders, wallets, exchange mutation or live trading.
