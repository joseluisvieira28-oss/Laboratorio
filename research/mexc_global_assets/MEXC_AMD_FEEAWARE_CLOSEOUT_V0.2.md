# MEXC AMD FEE-AWARE LARGE-LAG — CLOSEOUT V0.2

Date: 2026-10-04
Run: 37230631691
Branch: `mexc-amd-feeaware-v0.2-prereg-2026-10-04`

Frozen rule:
- external shock >= 20 bps
- lag gap >= 10 bps
- horizon = 1 minute
- FOLLOW_EXTERNAL_CONSENSUS
- no grid search

Result:
- sessions = 17
- exact common minutes = 4,573
- N = 5
- distinct signal sessions = 4
- wins = 5
- win rate = 100%
- mean gross = +14.798598 bps
- median gross = +12.027951 bps
- chronological thirds = +19.789425 / +9.070869 / +18.030913 bps
- one-sided binomial p = 0.03125

Frozen scientific gate required:
- N >= 20
- >= 8 distinct sessions
- positive mean/median
- win rate > 50%
- all thirds positive
- p < 0.05

Frozen execution-scale gate required:
- mean gross > 16 bps
- median gross > 12 bps

Verdict:
`FEEAWARE_AMD_UNDERPOWERED`

Scientific PASS = false because N/session coverage is insufficient.
Execution-scale PASS = false because scientific PASS is prerequisite and mean gross is below 16 bps.

Artifact SHA256:
`9bf0708145845bbd165738dabda64353e63eb8b71de3277b7aa1c5c33e79bfd9`

Interpretation:
The observed 5/5 wins and ~15 bps gross mean are suggestive but cannot be promoted. Thresholds must not be lowered or tuned after this result.

The predeclared untouched source-pass candidates NFLX, BABA, GOOGL and ORCL may be tested under the identical 20/10/1m rule only after a new pre-outcome multi-asset freeze with multiplicity control.

No private endpoints, account reads, wallets, orders, exchange mutation or live trading were used.
